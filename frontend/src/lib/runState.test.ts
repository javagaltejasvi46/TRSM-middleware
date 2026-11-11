import { describe, expect, it } from 'vitest';
import { deriveNodeStates, deriveRouteDecisions, formatMs, routeKey, runTiming } from './runState';
import { AuditEvent } from '../types';

let t = 0;
const ev = (over: Partial<AuditEvent>): AuditEvent => ({
  event_id: `e${++t}`,
  run_id: 'r1',
  trace_id: 't1',
  timestamp: new Date(Date.UTC(2026, 10, 11, 10, 0, 0, t * 10)).toISOString(),
  actor_id: 'orchestrator',
  event_type: 'workflow.started',
  trust_labels: [],
  ...over,
});

const NODES = ['backend_agent', 'db_manager_agent', 'qa_agent'];

/** Shape of a real benign run: backend reads a tool, messages db_manager, which is delivered. */
const benign = () => [
  ev({ event_type: 'workflow.started' }),
  ev({ event_type: 'resource.proposed', actor_id: 'backend_agent', target_id: 'customer_db' }),
  ev({ event_type: 'resource.policy_decided', actor_id: 'resource_gateway', target_id: 'customer_db', policy_decision: 'ALLOW' }),
  ev({ event_type: 'resource.executed', actor_id: 'backend_agent', target_id: 'customer_db', policy_decision: 'ALLOW' }),
  ev({ event_type: 'message.proposed', actor_id: 'backend_agent', target_id: 'db_manager_agent' }),
  ev({ event_type: 'message.policy_decided', actor_id: 'communication_gateway', target_id: 'db_manager_agent', policy_decision: 'ALLOW', reason_code: 'AUTHORIZED_PEER_COMMUNICATION' }),
  ev({ event_type: 'message.delivered', actor_id: 'backend_agent', target_id: 'db_manager_agent', policy_decision: 'ALLOW', reason_code: 'AUTHORIZED_PEER_COMMUNICATION' }),
  ev({ event_type: 'workflow.completed' }),
];

describe('deriveNodeStates', () => {
  it('marks agents that took part as completed and others as not reached', () => {
    const s = deriveNodeStates(benign(), NODES, 'completed');
    expect(s.backend_agent.status).toBe('completed');
    expect(s.db_manager_agent.status).toBe('completed'); // reached via message.delivered
    expect(s.qa_agent.status).toBe('not_reached');
    expect(s.qa_agent.eventCount).toBe(0);
    expect(s.backend_agent.spanMs).toBeGreaterThan(0);
  });

  it('marks the sender of a blocked message as blocked with its reason, and the recipient as not reached', () => {
    const events = [
      ev({ event_type: 'message.proposed', actor_id: 'backend_agent', target_id: 'db_manager_agent' }),
      ev({ event_type: 'message.blocked', actor_id: 'backend_agent', target_id: 'db_manager_agent', policy_decision: 'BLOCK', reason_code: 'THREAT_PROMPT_INJECTION' }),
    ];
    const s = deriveNodeStates(events, NODES, 'completed');
    expect(s.backend_agent.status).toBe('blocked');
    expect(s.backend_agent.reasons).toEqual(['THREAT_PROMPT_INJECTION']);
    expect(s.db_manager_agent.status).toBe('not_reached');
  });

  it('uses the most severe outcome: BLOCK > QUARANTINE > REVIEW', () => {
    const events = [
      ev({ event_type: 'resource.blocked', actor_id: 'qa_agent', target_id: 'deploy', policy_decision: 'REVIEW', reason_code: 'HIGH_RISK_OPERATION_REQUIRES_REVIEW' }),
      ev({ event_type: 'message.quarantined', actor_id: 'qa_agent', target_id: 'backend_agent', policy_decision: 'QUARANTINE', reason_code: 'THREAT_MEMORY_POISONING' }),
      ev({ event_type: 'resource.blocked', actor_id: 'db_manager_agent', target_id: 'deploy', policy_decision: 'REVIEW' }),
    ];
    const s = deriveNodeStates(events, NODES, 'completed');
    expect(s.qa_agent.status).toBe('quarantined');
    expect(s.qa_agent.reasons).toEqual(['HIGH_RISK_OPERATION_REQUIRES_REVIEW', 'THREAT_MEMORY_POISONING']);
    expect(s.db_manager_agent.status).toBe('review_required');
  });

  it('does not let gateway decisions (actor = gateway) mark an agent', () => {
    const events = [ev({ event_type: 'message.policy_decided', actor_id: 'communication_gateway', target_id: 'qa_agent', policy_decision: 'BLOCK' })];
    expect(deriveNodeStates(events, NODES, 'completed').qa_agent.status).toBe('not_reached');
  });

  it('marks participating agents failed when the backend reports the run failed', () => {
    const events = [ev({ event_type: 'resource.proposed', actor_id: 'backend_agent', target_id: 'x' })];
    expect(deriveNodeStates(events, NODES, 'failed').backend_agent.status).toBe('failed');
  });

  it('treats baseline (TRSM off) deliveries as completed, not blocked', () => {
    const events = [ev({ event_type: 'message.delivered', actor_id: 'backend_agent', target_id: 'qa_agent', policy_decision: 'ALLOW', reason_code: 'BASELINE_BYPASS' })];
    const s = deriveNodeStates(events, NODES, 'completed');
    expect(s.backend_agent.status).toBe('completed');
    expect(s.qa_agent.status).toBe('completed');
  });
});

describe('deriveRouteDecisions', () => {
  it('maps sender->recipient to the decision and reason from delivery/block events', () => {
    const d = deriveRouteDecisions(benign());
    expect(d[routeKey('backend_agent', 'db_manager_agent')]).toEqual({ decision: 'ALLOW', reasonCode: 'AUTHORIZED_PEER_COMMUNICATION' });
    // policy_decided has the gateway as actor, so it never creates a fake route
    expect(Object.keys(d)).toEqual(['backend_agent->db_manager_agent']);
  });

  it('keeps the most severe outcome when a route carried several messages', () => {
    const d = deriveRouteDecisions([
      ev({ event_type: 'message.delivered', actor_id: 'a', target_id: 'b', policy_decision: 'ALLOW' }),
      ev({ event_type: 'message.blocked', actor_id: 'a', target_id: 'b', policy_decision: 'BLOCK', reason_code: 'X' }),
      ev({ event_type: 'message.delivered', actor_id: 'a', target_id: 'b', policy_decision: 'ALLOW' }),
    ]);
    expect(d['a->b']).toEqual({ decision: 'BLOCK', reasonCode: 'X' });
  });
});

describe('runTiming / formatMs', () => {
  it('measures from workflow.started to workflow.completed', () => {
    const r = runTiming(benign());
    expect(r.startedAt).not.toBeNull();
    expect(r.durationMs).toBeGreaterThan(0);
  });
  it('returns nulls when the run has no workflow events', () => {
    expect(runTiming([])).toEqual({ startedAt: null, endedAt: null, durationMs: null });
  });
  it('formats durations', () => {
    expect(formatMs(null)).toBe('—');
    expect(formatMs(0.2)).toBe('<1 ms');
    expect(formatMs(42)).toBe('42 ms');
    expect(formatMs(1500)).toBe('1.50 s');
  });
});
