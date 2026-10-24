import React, { useState } from 'react';
import { AuditEvent, PolicyDecisionEnum } from '../../types';
import { ArrowRight, Search, Shield, Filter, Clock } from 'lucide-react';

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
  const [filterDecision, setFilterDecision] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

  const getDecisionBadge = (decision?: PolicyDecisionEnum | null) => {
    switch (decision) {
      case 'ALLOW':
        return <span className="badge-allow" style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700 }}>ALLOW</span>;
      case 'BLOCK':
        return <span className="badge-block" style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700 }}>BLOCK</span>;
      case 'QUARANTINE':
        return <span className="badge-quarantine" style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700 }}>QUARANTINE</span>;
      case 'REVIEW':
        return <span className="badge-review" style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700 }}>REVIEW</span>;
      default:
        return null;
    }
  };

  const filteredEvents = events.filter((evt) => {
    if (filterDecision !== 'ALL') {
      if (evt.policy_decision !== filterDecision) return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchActor = evt.actor_id.toLowerCase().includes(q);
      const matchTarget = evt.target_id?.toLowerCase().includes(q) || false;
      const matchType = evt.event_type.toLowerCase().includes(q);
      const matchReason = evt.reason_code?.toLowerCase().includes(q) || false;
      const matchSummary = evt.safe_payload_summary?.toLowerCase().includes(q) || false;
      return matchActor || matchTarget || matchType || matchReason || matchSummary;
    }
    return true;
  });

  return (
    <div className="glass-panel" style={{ padding: '18px', display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc' }}>Audit Trace Explorer</h3>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>{filteredEvents.length} of {events.length} causal events</span>
        </div>
      </div>

      {/* Search Input */}
      <div style={{ position: 'relative', marginBottom: '10px' }}>
        <Search size={14} color="#64748b" style={{ position: 'absolute', top: '9px', left: '10px' }} />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter by actor, resource, reason..."
          style={{
            width: '100%',
            padding: '7px 10px 7px 32px',
            background: 'rgba(15, 23, 42, 0.8)',
            border: '1px solid #334155',
            borderRadius: '6px',
            color: '#f8fafc',
            fontSize: '11px',
            outline: 'none',
          }}
        />
      </div>

      {/* Decision Filter Pills */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {['ALL', 'ALLOW', 'BLOCK', 'REVIEW', 'QUARANTINE'].map((d) => (
          <button
            key={d}
            onClick={() => setFilterDecision(d)}
            style={{
              padding: '3px 8px',
              borderRadius: '4px',
              fontSize: '10px',
              fontWeight: 600,
              cursor: 'pointer',
              background: filterDecision === d ? 'rgba(99, 102, 241, 0.3)' : 'rgba(30, 41, 59, 0.5)',
              color: filterDecision === d ? '#818cf8' : '#64748b',
              border: `1px solid ${filterDecision === d ? '#818cf8' : '#334155'}`,
            }}
          >
            {d}
          </button>
        ))}
      </div>

      {/* Event Stream */}
      <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '420px', flex: 1 }}>
        {filteredEvents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px 10px', color: '#64748b', fontSize: '12px' }}>
            No trace events match the selected criteria.
          </div>
        ) : (
          filteredEvents.map((evt) => {
            const isExpanded = expandedEventId === evt.event_id;
            return (
              <div
                key={evt.event_id}
                onClick={() => {
                  onSelectEvent?.(evt);
                  setExpandedEventId(isExpanded ? null : evt.event_id);
                }}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background:
                    selectedEventId === evt.event_id
                      ? 'rgba(99, 102, 241, 0.25)'
                      : 'rgba(30, 41, 59, 0.5)',
                  border: `1px solid ${selectedEventId === evt.event_id ? '#818cf8' : 'rgba(51, 65, 85, 0.5)'}`,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 600, fontSize: '12px', color: '#cbd5e1' }}>{evt.event_type}</span>
                  {getDecisionBadge(evt.policy_decision)}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>
                  <span style={{ color: '#818cf8', fontWeight: 600 }}>{evt.actor_id}</span>
                  {evt.target_id && (
                    <>
                      <ArrowRight size={10} color="#64748b" />
                      <span style={{ color: '#38bdf8' }}>{evt.target_id}</span>
                    </>
                  )}
                </div>

                {evt.safe_payload_summary && (
                  <div style={{ fontSize: '11px', color: '#94a3b8', fontStyle: 'italic', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    "{evt.safe_payload_summary}"
                  </div>
                )}

                {evt.reason_code && (
                  <div style={{ marginTop: '4px', fontSize: '10px', color: '#f43f5e', fontFamily: 'monospace' }}>
                    Reason: {evt.reason_code}
                  </div>
                )}

                {/* Expanded Details */}
                {isExpanded && (
                  <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #334155', fontSize: '10px', color: '#cbd5e1', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div>
                      <span style={{ color: '#64748b' }}>Event ID: </span>
                      <span style={{ fontFamily: 'monospace' }}>{evt.event_id}</span>
                    </div>
                    {evt.parent_event_id && (
                      <div>
                        <span style={{ color: '#64748b' }}>Parent Event: </span>
                        <span style={{ fontFamily: 'monospace' }}>{evt.parent_event_id}</span>
                      </div>
                    )}
                    {evt.duration_ms !== null && evt.duration_ms !== undefined && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={10} color="#64748b" />
                        <span>Duration: {evt.duration_ms.toFixed(2)}ms</span>
                      </div>
                    )}
                    {evt.trust_labels && evt.trust_labels.length > 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                        <span style={{ color: '#64748b' }}>Labels: </span>
                        {evt.trust_labels.map((lbl) => (
                          <span
                            key={lbl}
                            style={{
                              padding: '1px 5px',
                              borderRadius: '3px',
                              background: lbl === 'untrusted_external' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(99, 102, 241, 0.2)',
                              color: lbl === 'untrusted_external' ? '#f43f5e' : '#818cf8',
                              fontSize: '9px',
                              fontFamily: 'monospace',
                            }}
                          >
                            {lbl}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
