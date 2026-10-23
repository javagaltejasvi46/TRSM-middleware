import React from 'react';
import { AuditEvent, PolicyDecisionEnum } from '../../types';
import { ShieldCheck, ShieldX, ShieldAlert, Clock, ArrowRight } from 'lucide-react';

interface TraceExplorerProps {
  events: AuditEvent[];
  selectedEventId?: string;
  onSelectEvent?: (event: AuditEvent) => void;
}

export const TraceExplorer: React.FC<TraceExplorerProps> = ({
  events,
  selectedEventId,
  onSelectEvent,
}) => {
  const getDecisionBadge = (decision?: PolicyDecisionEnum | null) => {
    switch (decision) {
      case 'ALLOW':
        return <span className="badge-allow" style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>ALLOW</span>;
      case 'BLOCK':
        return <span className="badge-block" style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>BLOCK</span>;
      case 'QUARANTINE':
        return <span className="badge-quarantine" style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>QUARANTINE</span>;
      case 'REVIEW':
        return <span className="badge-review" style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>REVIEW</span>;
      default:
        return null;
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '18px', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>Causal Audit Trace Stream</h3>
        <span style={{ fontSize: '12px', color: '#64748b' }}>{events.length} events recorded</span>
      </div>

      <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '520px' }}>
        {events.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px', color: '#64748b', fontSize: '13px' }}>
            No trace events yet. Trigger a workflow execution run to observe live mediated events.
          </div>
        ) : (
          events.map((evt) => (
            <div
              key={evt.event_id}
              onClick={() => onSelectEvent?.(evt)}
              style={{
                padding: '10px 12px',
                borderRadius: '8px',
                background: selectedEventId === evt.event_id ? 'rgba(99, 102, 241, 0.2)' : 'rgba(30, 41, 59, 0.5)',
                border: `1px solid ${selectedEventId === evt.event_id ? '#818cf8' : 'rgba(51, 65, 85, 0.5)'}`,
                cursor: 'pointer',
                transition: 'background 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontWeight: 600, fontSize: '12px', color: '#cbd5e1' }}>{evt.event_type}</span>
                {getDecisionBadge(evt.policy_decision)}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>
                <span style={{ color: '#818cf8' }}>{evt.actor_id}</span>
                {evt.target_id && (
                  <>
                    <ArrowRight size={10} />
                    <span style={{ color: '#38bdf8' }}>{evt.target_id}</span>
                  </>
                )}
              </div>

              {evt.safe_payload_summary && (
                <div style={{ fontSize: '11px', color: '#64748b', fontStyle: 'italic', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  "{evt.safe_payload_summary}"
                </div>
              )}

              {evt.reason_code && (
                <div style={{ marginTop: '4px', fontSize: '10px', color: '#f43f5e', fontFamily: 'monospace' }}>
                  Reason: {evt.reason_code}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
