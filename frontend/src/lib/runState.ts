/**
 * Derive what the canvas shows after a run, strictly from backend audit events.
 *
 * The backend does not emit per-agent lifecycle events (agent.started/completed),
 * so node states here are a *view* computed from the message/resource events each
 * agent appears in, plus the run status the backend returned. Nothing is assumed
 * for agents that do not appear in any event: they are "not reached".
 */

import { AgentStatus, AuditEvent, PolicyDecisionEnum } from '../types';

/** AgentStatus from the backend contract, plus a frontend-only "never appeared in this run". */
export type NodeRunStatus = AgentStatus | 'not_reached';

export interface NodeRunState {
  status: NodeRunStatus;
  /** Number of audit events in which this agent is the actor or the message recipient. */
  eventCount: number;
  firstAt: string | null;
  lastAt: string | null;
  /** Time between this agent's first and last event, in ms (null with fewer than 2 events). */
  spanMs: number | null;
  /** Reason codes of this agent's non-ALLOW decisions, in order. */
  reasons: string[];
}

export interface RouteDecision {
  decision: PolicyDecisionEnum;
  reasonCode: string | null;
}

/** Events that record an agent's own action and its outcome (actor_id = the agent). */
const OUTCOME_EVENTS = new Set(['message.delivered', 'message.blocked', 'message.quarantined', 'resource.executed', 'resource.blocked']);

const SEVERITY: Partial<Record<PolicyDecisionEnum, { rank: number; status: AgentStatus }>> = {
  BLOCK: { rank: 3, status: 'blocked' },
  QUARANTINE: { rank: 2, status: 'quarantined' },
  REVIEW: { rank: 1, status: 'review_required' },
};

export const routeKey = (source: string, target: string) => `${source}->${target}`;

export function deriveNodeStates(events: AuditEvent[], nodeIds: string[], runStatus: string): Record<string, NodeRunState> {
  const ids = new Set(nodeIds);
  const out: Record<string, NodeRunState> = {};
  const worst: Record<string, number> = {};
  for (const id of nodeIds) {
    out[id] = { status: 'not_reached', eventCount: 0, firstAt: null, lastAt: null, spanMs: null, reasons: [] };
    worst[id] = 0;
  }

  const touch = (id: string, ts: string) => {
    const s = out[id];
    s.eventCount += 1;
    if (!s.firstAt || ts < s.firstAt) s.firstAt = ts;
    if (!s.lastAt || ts > s.lastAt) s.lastAt = ts;
  };

  for (const e of events) {
    const ts = String(e.timestamp);
    if (ids.has(e.actor_id)) touch(e.actor_id, ts);
    // A delivered message means the recipient was reached.
    if (e.event_type === 'message.delivered' && e.target_id && ids.has(e.target_id) && e.target_id !== e.actor_id) touch(e.target_id, ts);

    if (ids.has(e.actor_id) && OUTCOME_EVENTS.has(e.event_type) && e.policy_decision && e.policy_decision !== 'ALLOW') {
      const sev = SEVERITY[e.policy_decision];
      if (sev && sev.rank > worst[e.actor_id]) worst[e.actor_id] = sev.rank;
      if (e.reason_code && !out[e.actor_id].reasons.includes(e.reason_code)) out[e.actor_id].reasons.push(e.reason_code);
    }
  }

  const rankToStatus: Record<number, AgentStatus> = { 3: 'blocked', 2: 'quarantined', 1: 'review_required' };
  for (const id of nodeIds) {
    const s = out[id];
    if (s.firstAt && s.lastAt && s.eventCount > 1) s.spanMs = new Date(s.lastAt).getTime() - new Date(s.firstAt).getTime();
    if (s.eventCount === 0) continue;
    if (worst[id] > 0) s.status = rankToStatus[worst[id]];
    else if (runStatus === 'failed') s.status = 'failed';
    else if (runStatus === 'completed') s.status = 'completed';
    else s.status = 'running';
  }
  return out;
}

/** The gateway's decision for each sender -> recipient message, from the delivery/block events. */
export function deriveRouteDecisions(events: AuditEvent[]): Record<string, RouteDecision> {
  const out: Record<string, RouteDecision> = {};
  for (const e of events) {
    if (!e.target_id || !e.policy_decision) continue;
    if (e.event_type !== 'message.delivered' && e.event_type !== 'message.blocked' && e.event_type !== 'message.quarantined') continue;
    const key = routeKey(e.actor_id, e.target_id);
    const prev = out[key];
    // If a route carried several messages, show the most severe outcome.
    const rank = (d: PolicyDecisionEnum) => SEVERITY[d]?.rank ?? 0;
    if (!prev || rank(e.policy_decision) > rank(prev.decision)) out[key] = { decision: e.policy_decision, reasonCode: e.reason_code ?? null };
  }
  return out;
}

/** Start/end of the run from its workflow.* events (null when absent). */
export function runTiming(events: AuditEvent[]): { startedAt: string | null; endedAt: string | null; durationMs: number | null } {
  const start = events.find((e) => e.event_type === 'workflow.started');
  const end = [...events].reverse().find((e) => e.event_type === 'workflow.completed' || e.event_type === 'workflow.failed');
  const startedAt = start ? String(start.timestamp) : null;
  const endedAt = end ? String(end.timestamp) : null;
  const durationMs = startedAt && endedAt ? new Date(endedAt).getTime() - new Date(startedAt).getTime() : null;
  return { startedAt, endedAt, durationMs };
}

export const formatMs = (ms: number | null) => (ms === null ? '—' : ms < 1 ? '<1 ms' : ms < 1000 ? `${ms.toFixed(0)} ms` : `${(ms / 1000).toFixed(2)} s`);
