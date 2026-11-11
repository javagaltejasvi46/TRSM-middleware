import { describe, expect, it } from 'vitest';
import { EMPTY_FILTERS, filterEvents, filterOptions, formatEventTime, isFiltering } from './traceFilters';
import { AuditEvent } from '../types';

const ev = (over: Partial<AuditEvent>): AuditEvent => ({
  event_id: Math.random().toString(36).slice(2),
  run_id: 'r1',
  trace_id: 't1',
  timestamp: '2026-11-11T10:00:00.000Z',
  actor_id: 'backend_agent',
  event_type: 'message.proposed',
  trust_labels: [],
  ...over,
});

const events = [
  ev({ event_type: 'workflow.started', actor_id: 'orchestrator', target_id: 'wf' }),
  ev({ event_type: 'message.policy_decided', actor_id: 'communication_gateway', target_id: 'db_manager_agent', policy_decision: 'ALLOW', reason_code: 'AUTHORIZED_PEER_COMMUNICATION' }),
  ev({ event_type: 'message.blocked', actor_id: 'backend_agent', target_id: 'qa_agent', policy_decision: 'BLOCK', reason_code: 'THREAT_PROMPT_INJECTION', safe_payload_summary: 'IGNORE PREVIOUS INSTRUCTIONS' }),
  ev({ event_type: 'message.quarantined', actor_id: 'db_manager_agent', target_id: 'qa_agent', policy_decision: 'QUARANTINE' }),
];

describe('filterEvents', () => {
  it('returns everything with no filters, in the original order', () => {
    expect(filterEvents(events, EMPTY_FILTERS)).toEqual(events);
    expect(isFiltering(EMPTY_FILTERS)).toBe(false);
  });

  it('filters by agent as either actor or target', () => {
    const got = filterEvents(events, { ...EMPTY_FILTERS, agent: 'qa_agent' });
    expect(got.map((e) => e.event_type)).toEqual(['message.blocked', 'message.quarantined']);
    const asActor = filterEvents(events, { ...EMPTY_FILTERS, agent: 'db_manager_agent' });
    expect(asActor).toHaveLength(2);
  });

  it('filters by decision, including events with no decision', () => {
    expect(filterEvents(events, { ...EMPTY_FILTERS, decision: 'BLOCK' }).map((e) => e.event_type)).toEqual(['message.blocked']);
    expect(filterEvents(events, { ...EMPTY_FILTERS, decision: 'none' }).map((e) => e.event_type)).toEqual(['workflow.started']);
  });

  it('filters by event type and combines filters with AND', () => {
    expect(filterEvents(events, { ...EMPTY_FILTERS, eventType: 'message.quarantined' })).toHaveLength(1);
    expect(filterEvents(events, { ...EMPTY_FILTERS, agent: 'qa_agent', decision: 'ALLOW' })).toEqual([]);
  });

  it('searches reason codes and payload summaries case-insensitively', () => {
    expect(filterEvents(events, { ...EMPTY_FILTERS, search: 'prompt_injection' })).toHaveLength(1);
    expect(filterEvents(events, { ...EMPTY_FILTERS, search: '  ignore previous ' })).toHaveLength(1);
    expect(isFiltering({ ...EMPTY_FILTERS, search: '   ' })).toBe(false);
  });
});

describe('filterOptions / formatEventTime', () => {
  it('lists distinct sorted agents, types and decisions present', () => {
    const o = filterOptions(events);
    expect(o.agents).toEqual(['backend_agent', 'communication_gateway', 'db_manager_agent', 'orchestrator', 'qa_agent', 'wf']);
    expect(o.decisions).toEqual(['ALLOW', 'BLOCK', 'QUARANTINE']);
    expect(o.types).toContain('message.blocked');
  });

  it('formats a timestamp with milliseconds and passes through unparseable input', () => {
    expect(formatEventTime('2026-11-11T10:00:00.042Z')).toMatch(/^\d{2}:\d{2}:\d{2}\.042$/);
    expect(formatEventTime('not a date')).toBe('not a date');
  });
});
