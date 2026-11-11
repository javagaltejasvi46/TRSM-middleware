import React, { useState } from 'react';
import { Check, Copy, CornerLeftUp, CornerDownRight, Info } from 'lucide-react';
import { AuditEvent } from '../../types';
import { ancestry, parentOf, type EventIndex } from '../../lib/traceLinks';
import { formatEventTime } from '../../lib/traceFilters';
import { formatMs } from '../../lib/runState';

interface EventDetailProps {
  event: AuditEvent;
  index: EventIndex;
  onSelect: (eventId: string) => void;
}

const Row: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <div style={{ display: 'grid', gridTemplateColumns: '92px minmax(0, 1fr)', gap: '8px', alignItems: 'baseline' }}>
    <dt style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)' }}>{label}</dt>
    <dd style={{ fontSize: '12px', color: 'var(--text-primary)', minWidth: 0, overflowWrap: 'anywhere' }}>{children}</dd>
  </div>
);

const Mono: React.FC<{ children: React.ReactNode }> = ({ children }) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{children}</span>;

const NotRecorded: React.FC<{ what: string }> = ({ what }) => (
  <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>{what} not recorded by the backend</span>
);

const linkBtn: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  background: 'none',
  border: 'none',
  padding: '2px 0',
  color: 'var(--accent-text)',
  fontWeight: 600,
  fontSize: '12px',
  cursor: 'pointer',
  textDecoration: 'underline',
  textUnderlineOffset: 2,
  textAlign: 'left',
};

const CopyId: React.FC<{ value: string; label: string }> = ({ value, label }) => {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      aria-label={copied ? `${label} copied` : `Copy ${label}`}
      onClick={() => {
        navigator.clipboard?.writeText(value).then(
          () => {
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
          },
          () => undefined,
        );
      }}
      style={{ display: 'inline-flex', verticalAlign: 'middle', marginLeft: 4, padding: 3, border: '1px solid var(--border-color)', borderRadius: 6, background: '#ffffff', color: 'var(--text-secondary)', cursor: 'pointer' }}
    >
      {copied ? <Check size={11} aria-hidden="true" /> : <Copy size={11} aria-hidden="true" />}
    </button>
  );
};

/**
 * Full record for one audit event. Shows only what the backend recorded:
 * missing causal links and trust labels are stated as missing, never inferred.
 * Metadata values are not rendered (only field names) so unredacted payloads
 * cannot leak into the trace view.
 */
export const EventDetail: React.FC<EventDetailProps> = ({ event: e, index, onSelect }) => {
  const parent = parentOf(e, index);
  const children = index.children.get(e.event_id) ?? [];
  const chain = ancestry(e, index);
  const metaKeys = Object.keys(e.payload_metadata ?? {});

  return (
    <div style={{ borderTop: '1px dashed var(--border-strong)', marginTop: '8px', paddingTop: '8px' }}>
      <dl style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
        <Row label="Event ID">
          <Mono>{e.event_id}</Mono>
          <CopyId value={e.event_id} label="event ID" />
        </Row>
        <Row label="Trace ID">
          <Mono>{e.trace_id}</Mono>
        </Row>
        <Row label="Run ID">
          <Mono>{e.run_id}</Mono>
        </Row>
        <Row label="Time">
          <time dateTime={e.timestamp}>
            <Mono>{formatEventTime(e.timestamp)}</Mono>
          </time>{' '}
          <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>({e.timestamp})</span>
        </Row>
        <Row label="From → to">
          <Mono>{e.actor_id}</Mono> → {e.target_id ? <Mono>{e.target_id}</Mono> : <span style={{ color: 'var(--text-muted)' }}>no target</span>}
        </Row>
        <Row label="Decision">{e.policy_decision ?? <span style={{ color: 'var(--text-muted)' }}>none (not a decision event)</span>}</Row>
        <Row label="Reason">{e.reason_code ? <Mono>{e.reason_code}</Mono> : <span style={{ color: 'var(--text-muted)' }}>—</span>}</Row>
        <Row label="Policy ver.">{e.policy_version ?? '—'}</Row>
        <Row label="Duration">{e.duration_ms == null ? <span style={{ color: 'var(--text-muted)' }}>not recorded</span> : formatMs(e.duration_ms)}</Row>
        <Row label="Trust labels">
          {e.trust_labels.length ? (
            <span style={{ display: 'inline-flex', flexWrap: 'wrap', gap: '4px' }}>
              {e.trust_labels.map((t) => (
                <span key={t} className={t === 'untrusted_external' ? 'badge badge-quarantine' : 'badge badge-review'}>{t}</span>
              ))}
            </span>
          ) : (
            <NotRecorded what="Trust labels" />
          )}
        </Row>
        <Row label="Parent">
          {parent.kind === 'none' && <NotRecorded what="Parent link" />}
          {parent.kind === 'in-run' && (
            <button type="button" style={linkBtn} onClick={() => onSelect(parent.parent.event_id)}>
              <CornerLeftUp size={12} aria-hidden="true" /> {parent.parent.event_type} ({parent.parent.actor_id})
            </button>
          )}
          {parent.kind === 'missing' && (
            <span>
              <Mono>{parent.parentId}</Mono> <span style={{ color: 'var(--warn-text)' }}>(not among this run's events)</span>
            </span>
          )}
        </Row>
        <Row label="Children">
          {children.length === 0 ? (
            <span style={{ color: 'var(--text-muted)' }}>{index.hasAnyLinks ? 'none' : <NotRecorded what="Child links" />}</span>
          ) : (
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {children.map((c) => (
                <li key={c.event_id}>
                  <button type="button" style={linkBtn} onClick={() => onSelect(c.event_id)}>
                    <CornerDownRight size={12} aria-hidden="true" /> {c.event_type} ({c.actor_id})
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Row>
        {chain.length > 1 && (
          <Row label="Causal chain">
            <ol aria-label="Causal chain from root" style={{ listStyle: 'none', display: 'flex', flexWrap: 'wrap', gap: '4px', alignItems: 'center' }}>
              {chain.map((c, i) => (
                <li key={c.event_id} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  {i > 0 && <span aria-hidden="true" style={{ color: 'var(--text-muted)' }}>→</span>}
                  {c.event_id === e.event_id ? (
                    <strong style={{ fontSize: '11px', fontFamily: 'var(--font-mono)' }} aria-current="true">{c.event_type}</strong>
                  ) : (
                    <button type="button" style={{ ...linkBtn, fontSize: '11px', fontFamily: 'var(--font-mono)' }} onClick={() => onSelect(c.event_id)}>
                      {c.event_type}
                    </button>
                  )}
                </li>
              ))}
            </ol>
          </Row>
        )}
        <Row label="Metadata">
          {metaKeys.length === 0 ? (
            <span style={{ color: 'var(--text-muted)' }}>none</span>
          ) : (
            <span>
              {metaKeys.length} field{metaKeys.length > 1 ? 's' : ''}: <Mono>{metaKeys.join(', ')}</Mono>{' '}
              <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>(values not shown)</span>
            </span>
          )}
        </Row>
      </dl>
      {!index.hasAnyLinks && (
        <p style={{ display: 'flex', gap: '6px', marginTop: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
          <Info size={12} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} />
          No event in this run has a parent link, so the causal chain cannot be shown. The links appear here once the backend records parent_event_id.
        </p>
      )}
    </div>
  );
};
