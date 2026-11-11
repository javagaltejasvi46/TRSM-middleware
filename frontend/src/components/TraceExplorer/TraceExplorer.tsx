import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AuditEvent, PolicyDecisionEnum } from '../../types';
import {
  AlertTriangle,
  ArrowRight,
  Brain,
  Eye,
  FlaskConical,
  MessageSquare,
  Search,
  ShieldAlert,
  ShieldCheck,
  ShieldQuestion,
  ShieldX,
  Workflow,
  Wrench,
  X,
} from 'lucide-react';
import { EventDetail } from './EventDetail';
import { buildEventIndex } from '../../lib/traceLinks';
import { EMPTY_FILTERS, eventFamily, filterEvents, filterOptions, formatEventTime, isFiltering, type TraceFilters } from '../../lib/traceFilters';

interface TraceExplorerProps {
  events: AuditEvent[];
  selectedEventId?: string;
  onSelectEvent?: (event: AuditEvent) => void;
  /** Set from outside (e.g. "View events" on an agent) to filter the trace to one agent. */
  focusAgent?: { id: string; nonce: number } | null;
}

const DECISION_BADGE: Record<PolicyDecisionEnum, { cls: string; Icon: React.ElementType }> = {
  ALLOW: { cls: 'badge-allow', Icon: ShieldCheck },
  BLOCK: { cls: 'badge-block', Icon: ShieldX },
  QUARANTINE: { cls: 'badge-quarantine', Icon: ShieldAlert },
  REVIEW: { cls: 'badge-review', Icon: ShieldQuestion },
};

const FAMILY_ICON: Record<string, React.ElementType> = {
  workflow: Workflow,
  agent: Brain,
  message: MessageSquare,
  resource: Wrench,
  memory: Brain,
  threat: AlertTriangle,
  review: Eye,
  evaluation: FlaskConical,
};

/** Rail dot colour follows the decision so blocked/quarantined events stand out (icon + badge text too). */
const dotTone = (d?: PolicyDecisionEnum | null) =>
  d === 'BLOCK' ? 'badge-block' : d === 'QUARANTINE' ? 'badge-quarantine' : d === 'REVIEW' ? 'badge-review' : d === 'ALLOW' ? 'badge-allow' : '';

export const TraceExplorer: React.FC<TraceExplorerProps> = ({ events, selectedEventId, onSelectEvent, focusAgent }) => {
  const [filters, setFilters] = useState<TraceFilters>(EMPTY_FILTERS);
  const [openId, setOpenId] = useState<string | null>(null);
  const focusAfterRender = useRef<string | null>(null);
  // A new run's events replace the old ones: start unfiltered, nothing open.
  useEffect(() => {
    setFilters(EMPTY_FILTERS);
    setOpenId(null);
  }, [events]);
  useEffect(() => {
    if (focusAgent) setFilters({ ...EMPTY_FILTERS, agent: focusAgent.id });
  }, [focusAgent]);
  const options = useMemo(() => filterOptions(events), [events]);
  const visible = useMemo(() => filterEvents(events, filters), [events, filters]);
  const filtering = isFiltering(filters);
  const set = <K extends keyof TraceFilters>(k: K, v: TraceFilters[K]) => setFilters((f) => ({ ...f, [k]: v }));
  const index = useMemo(() => buildEventIndex(events), [events]);
  const activeId = selectedEventId ?? openId;
  const domId = (id: string) => `trace-evt-${id}`;

  const toggle = (evt: AuditEvent) => {
    setOpenId((cur) => (cur === evt.event_id ? null : evt.event_id));
    onSelectEvent?.(evt);
  };

  // Jump to a linked (parent/child) event: open it, reveal it if filtered out, and move focus to it.
  const jumpTo = (id: string) => {
    const target = index.byId.get(id);
    if (!target) return;
    if (!filterEvents([target], filters).length) setFilters(EMPTY_FILTERS);
    setOpenId(id);
    focusAfterRender.current = id;
    onSelectEvent?.(target);
  };
  useEffect(() => {
    const id = focusAfterRender.current;
    if (!id) return;
    focusAfterRender.current = null;
    const el = document.getElementById(domId(id));
    el?.scrollIntoView?.({ block: 'nearest' });
    el?.focus();
  });

  return (
    <section className="surface" aria-labelledby="trace-title" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '8px' }}>
        <h3 id="trace-title" style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>Causal Audit Trace</h3>
        <span role="status" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          {filtering ? `Showing ${visible.length} of ${events.length} events` : `${events.length} events recorded`}
        </span>
      </div>

      {events.length > 0 && (
        <div role="search" aria-label="Filter trace events" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <div style={{ gridColumn: '1 / -1', position: 'relative' }}>
            <Search size={14} aria-hidden="true" style={{ position: 'absolute', left: 10, top: 11, color: 'var(--text-muted)' }} />
            <input
              aria-label="Search events"
              className="field-input"
              placeholder="Search type, agent, reason…"
              value={filters.search}
              onChange={(e) => set('search', e.target.value)}
              style={{ paddingLeft: 30 }}
            />
          </div>
          <select aria-label="Filter by agent" className="field-input" value={filters.agent} onChange={(e) => set('agent', e.target.value)}>
            <option value="">All agents</option>
            {options.agents.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <select aria-label="Filter by decision" className="field-input" value={filters.decision} onChange={(e) => set('decision', e.target.value as TraceFilters['decision'])}>
            <option value="">All decisions</option>
            {options.decisions.map((d) => <option key={d} value={d}>{d}</option>)}
            <option value="none">No decision</option>
          </select>
          <select aria-label="Filter by event type" className="field-input" value={filters.eventType} onChange={(e) => set('eventType', e.target.value)}>
            <option value="">All event types</option>
            {options.types.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <select aria-label="Filter by threat type" className="field-input" value={filters.threat} onChange={(e) => set('threat', e.target.value)} disabled={options.threats.length === 0}>
            <option value="">{options.threats.length ? 'All threat types' : 'No threats in run'}</option>
            {options.threats.map((t) => <option key={t} value={t}>{t.replace(/^THREAT_/, '').toLowerCase().replace(/_/g, ' ')}</option>)}
          </select>
          {filtering && (
            <button type="button" className="btn btn-secondary" onClick={() => setFilters(EMPTY_FILTERS)} style={{ gridColumn: '1 / -1', minHeight: 32 }}>
              <X size={13} aria-hidden="true" /> Clear filters
            </button>
          )}
        </div>
      )}

      <div style={{ overflowY: 'auto', maxHeight: '520px', padding: '2px' }}>
        {events.length === 0 ? (
          <div className="well" style={{ textAlign: 'center', padding: '28px 16px', color: 'var(--text-secondary)', fontSize: '13px' }}>
            No trace events yet. Execute a run to see each mediated message and tool call.
          </div>
        ) : visible.length === 0 ? (
          <div className="well" style={{ textAlign: 'center', padding: '24px 16px', color: 'var(--text-secondary)', fontSize: '13px' }}>
            No events match these filters.{' '}
            <button type="button" onClick={() => setFilters(EMPTY_FILTERS)} style={{ background: 'none', border: 'none', color: 'var(--accent-text)', fontWeight: 600, cursor: 'pointer', textDecoration: 'underline', font: 'inherit' }}>
              Clear filters
            </button>
          </div>
        ) : (
          <ol aria-label="Trace events" style={{ listStyle: 'none', position: 'relative' }}>
            {visible.map((evt, i) => {
              const selected = activeId === evt.event_id;
              const Icon = FAMILY_ICON[eventFamily(evt.event_type)] ?? Workflow;
              const badge = evt.policy_decision ? DECISION_BADGE[evt.policy_decision] : null;
              const flagged = evt.policy_decision === 'BLOCK' || evt.policy_decision === 'QUARANTINE';
              const edge = selected ? 'var(--accent-primary)' : flagged ? (evt.policy_decision === 'BLOCK' ? '#fecaca' : '#fde68a') : 'var(--border-color)';
              return (
                <li key={evt.event_id} style={{ position: 'relative', display: 'flex', gap: '10px', paddingBottom: i < visible.length - 1 ? '10px' : 0 }}>
                  {/* Timeline rail */}
                  {i < visible.length - 1 && <span aria-hidden="true" style={{ position: 'absolute', left: 13, top: 30, bottom: 0, width: 2, background: 'var(--border-color)', borderRadius: 1 }} />}
                  <span
                    aria-hidden="true"
                    className={dotTone(evt.policy_decision) || 'icon-chip'}
                    style={{ flexShrink: 0, width: 28, height: 28, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', borderRadius: 9999, zIndex: 1, padding: 0, background: dotTone(evt.policy_decision) ? undefined : '#ffffff' }}
                  >
                    <Icon size={13} />
                  </span>

                  <div
                    className="well"
                    style={{
                      flex: 1,
                      minWidth: 0,
                      padding: '9px 11px',
                      background: selected ? 'var(--accent-soft)' : '#ffffff',
                      // Per-side colours (no shorthand) so the flagged left edge never conflicts on re-render.
                      borderTopColor: edge,
                      borderRightColor: edge,
                      borderBottomColor: edge,
                      borderLeftColor: flagged ? (evt.policy_decision === 'BLOCK' ? 'var(--status-block)' : 'var(--status-quarantine)') : edge,
                      borderLeftWidth: flagged ? 3 : 1,
                      boxShadow: '0 1px 2px rgba(30, 27, 75, 0.05)',
                    }}
                  >
                    <button
                      type="button"
                      id={domId(evt.event_id)}
                      aria-expanded={selected}
                      aria-controls={`${domId(evt.event_id)}-detail`}
                      onClick={() => toggle(evt)}
                      style={{ display: 'block', width: '100%', textAlign: 'left', background: 'none', border: 'none', padding: 0, font: 'inherit', color: 'inherit', cursor: 'pointer', borderRadius: 6 }}
                    >
                      <span style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 600, fontSize: '12px', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{evt.event_type}</span>
                        <time dateTime={evt.timestamp} style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                          {formatEventTime(evt.timestamp)}
                        </time>
                      </span>

                      <span style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '6px', fontSize: '12px', marginTop: '4px' }}>
                        <span style={{ color: 'var(--accent-text)', fontWeight: 600 }}>{evt.actor_id}</span>
                        {evt.target_id && (
                          <>
                            <ArrowRight size={11} aria-label="to" />
                            <span style={{ color: 'var(--info-text)', fontWeight: 600 }}>{evt.target_id}</span>
                          </>
                        )}
                        {badge && (
                          <span className={`badge ${badge.cls}`} style={{ marginLeft: 'auto' }}>
                            <badge.Icon size={12} aria-hidden="true" />
                            {evt.policy_decision}
                          </span>
                        )}
                      </span>

                      {evt.safe_payload_summary && (
                        <span style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', fontStyle: 'italic', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: '4px' }}>
                          "{evt.safe_payload_summary}"
                        </span>
                      )}

                      {(evt.reason_code || evt.trust_labels.length > 0) && (
                        <span style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
                          {evt.reason_code && (
                            <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', background: 'var(--surface-sunken)', border: '1px solid var(--border-color)', borderRadius: 6, padding: '1px 6px' }}>
                              {evt.reason_code}
                            </span>
                          )}
                          {evt.trust_labels.map((t) => (
                            <span key={t} title="Trust label" style={{ fontSize: '11px', color: 'var(--text-secondary)', border: '1px solid var(--border-strong)', borderRadius: 9999, padding: '0 7px' }}>
                              {t}
                            </span>
                          ))}
                        </span>
                      )}
                    </button>
                    {selected && (
                      <div id={`${domId(evt.event_id)}-detail`} role="region" aria-label={`Details for ${evt.event_type}`}>
                        <EventDetail event={evt} index={index} onSelect={jumpTo} />
                      </div>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </div>
    </section>
  );
};
