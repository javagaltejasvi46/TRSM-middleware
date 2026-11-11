/**
 * Filtering for the audit trace view. Filters only hide events from view; they
 * never change or reorder what the backend returned.
 */

import { AuditEvent, PolicyDecisionEnum } from '../types';

export interface TraceFilters {
  /** Matches an event whose actor_id OR target_id equals this agent/component. */
  agent: string;
  /** Exact event_type, e.g. "message.blocked". */
  eventType: string;
  /** A policy decision, or "none" for events that carry no decision. */
  decision: PolicyDecisionEnum | 'none' | '';
  /** A THREAT_* reason code emitted by the Policy Engine, e.g. "THREAT_PROMPT_INJECTION". */
  threat: string;
  /** Case-insensitive search over type, actor, target, reason and payload summary. */
  search: string;
}

export const EMPTY_FILTERS: TraceFilters = { agent: '', eventType: '', decision: '', threat: '', search: '' };

export const isFiltering = (f: TraceFilters) => Boolean(f.agent || f.eventType || f.decision || f.threat || f.search.trim());

/** Threat reason codes come from the Policy Engine as THREAT_<FAMILY>. */
export const isThreatReason = (code?: string | null): code is string => Boolean(code && code.startsWith('THREAT_'));

export function filterEvents(events: AuditEvent[], f: TraceFilters): AuditEvent[] {
  const needle = f.search.trim().toLowerCase();
  return events.filter((e) => {
    if (f.agent && e.actor_id !== f.agent && e.target_id !== f.agent) return false;
    if (f.eventType && e.event_type !== f.eventType) return false;
    if (f.decision === 'none' && e.policy_decision) return false;
    if (f.decision && f.decision !== 'none' && e.policy_decision !== f.decision) return false;
    if (f.threat && e.reason_code !== f.threat) return false;
    if (needle) {
      const hay = [e.event_type, e.actor_id, e.target_id, e.reason_code, e.safe_payload_summary].filter(Boolean).join(' ').toLowerCase();
      if (!hay.includes(needle)) return false;
    }
    return true;
  });
}

/** Distinct, sorted values present in the events, for the filter dropdowns. */
export function filterOptions(events: AuditEvent[]) {
  const agents = new Set<string>();
  const types = new Set<string>();
  const decisions = new Set<PolicyDecisionEnum>();
  const threats = new Set<string>();
  for (const e of events) {
    if (isThreatReason(e.reason_code)) threats.add(e.reason_code);
    agents.add(e.actor_id);
    if (e.target_id) agents.add(e.target_id);
    types.add(e.event_type);
    if (e.policy_decision) decisions.add(e.policy_decision);
  }
  return { agents: [...agents].sort(), types: [...types].sort(), decisions: [...decisions].sort(), threats: [...threats].sort() };
}

/** "message.blocked" -> "message"; used to pick an icon per event family. */
export const eventFamily = (type: string) => type.split('.')[0] ?? type;

/** Local wall-clock time with milliseconds, e.g. "14:03:07.412". */
export function formatEventTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const pad = (n: number, w = 2) => String(n).padStart(w, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}.${pad(d.getMilliseconds(), 3)}`;
}
