/**
 * Causal links between audit events, exactly as recorded by the backend
 * (parent_event_id). No links are inferred: if the backend did not record a
 * parent, there is no parent.
 */

import { AuditEvent } from '../types';

export interface EventIndex {
  byId: Map<string, AuditEvent>;
  /** parent event_id -> child events, in the order they were returned. */
  children: Map<string, AuditEvent[]>;
  /** True when at least one event in the run carries a parent_event_id. */
  hasAnyLinks: boolean;
}

export function buildEventIndex(events: AuditEvent[]): EventIndex {
  const byId = new Map<string, AuditEvent>();
  const children = new Map<string, AuditEvent[]>();
  let hasAnyLinks = false;
  for (const e of events) byId.set(e.event_id, e);
  for (const e of events) {
    if (!e.parent_event_id) continue;
    hasAnyLinks = true;
    const list = children.get(e.parent_event_id) ?? [];
    list.push(e);
    children.set(e.parent_event_id, list);
  }
  return { byId, children, hasAnyLinks };
}

export type ParentLink =
  | { kind: 'none' }
  | { kind: 'in-run'; parent: AuditEvent }
  /** A parent id was recorded but that event is not among this run's events. */
  | { kind: 'missing'; parentId: string };

export function parentOf(e: AuditEvent, index: EventIndex): ParentLink {
  if (!e.parent_event_id) return { kind: 'none' };
  const parent = index.byId.get(e.parent_event_id);
  return parent ? { kind: 'in-run', parent } : { kind: 'missing', parentId: e.parent_event_id };
}

/** Chain from the root down to (and including) this event, following recorded parents only. Stops on cycles. */
export function ancestry(e: AuditEvent, index: EventIndex): AuditEvent[] {
  const chain: AuditEvent[] = [e];
  const seen = new Set([e.event_id]);
  let cur = e;
  while (cur.parent_event_id) {
    const p = index.byId.get(cur.parent_event_id);
    if (!p || seen.has(p.event_id)) break;
    chain.unshift(p);
    seen.add(p.event_id);
    cur = p;
  }
  return chain;
}
