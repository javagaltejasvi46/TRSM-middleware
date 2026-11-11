import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Clock, ListFilter, Loader2, ServerCrash, Shield, ShieldOff } from 'lucide-react';
import { RunSummary } from '../../types';
import { TrsmNodeGuardBadge } from '../TrsmNodeGuardBadge/TrsmNodeGuardBadge';
import { formatMs, type NodeRunState } from '../../lib/runState';
import { formatEventTime } from '../../lib/traceFilters';

export type RunPanelState =
  | { kind: 'idle' }
  | { kind: 'running'; enableTrsm: boolean; sentAt: string }
  | { kind: 'error'; message: string }
  | {
      kind: 'done';
      summary: RunSummary;
      timing: { startedAt: string | null; endedAt: string | null; durationMs: number | null };
      nodeStates: Record<string, NodeRunState> | null;
      eventsError: string | null;
      metricsError: string | null;
      /** True when the canvas was edited after this run; overlays are then hidden. */
      stale: boolean;
    };

interface RunStatusPanelProps {
  state: RunPanelState;
  onViewAgentEvents: (nodeId: string) => void;
}

const Stat: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
  <div className="well" style={{ padding: '6px 10px', background: '#ffffff' }}>
    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{label}</div>
    <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>{value}</div>
  </div>
);

const Notice: React.FC<{ tone: 'warn' | 'error'; children: React.ReactNode }> = ({ tone, children }) => (
  <div
    role={tone === 'error' ? 'alert' : 'status'}
    className={tone === 'error' ? 'badge-block' : 'badge-quarantine'}
    style={{ display: 'flex', gap: '6px', fontSize: '12px', fontWeight: 500, borderRadius: 10, padding: '8px 10px' }}
  >
    {tone === 'error' ? <AlertCircle size={13} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} /> : <AlertTriangle size={13} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} />}
    <span>{children}</span>
  </div>
);

export const RunStatusPanel: React.FC<RunStatusPanelProps> = ({ state, onViewAgentEvents }) => {
  return (
    <section className="surface" aria-labelledby="run-status-title" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <h3 id="run-status-title" style={{ fontSize: '14px', fontWeight: 700 }}>Run status</h3>

      {state.kind === 'idle' && <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>No run yet. Execute a run to see what the backend decided.</p>}

      {state.kind === 'running' && (
        <p role="status" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--accent-text)' }}>
          <Loader2 size={15} className="animate-spin" aria-hidden="true" />
          Running on the backend ({state.enableTrsm ? 'TRSM protected' : 'baseline, no TRSM'}). Results appear when the run finishes.
        </p>
      )}

      {state.kind === 'error' && (
        <Notice tone="error">
          <strong>Run failed to start or finish.</strong> {state.message}
          <br />
          Nothing below reflects a run; no result is shown for a request that failed.
        </Notice>
      )}

      {state.kind === 'done' && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span className={`badge ${state.summary.status === 'completed' ? 'badge-allow' : 'badge-block'}`} style={{ fontSize: '12px' }}>
              {state.summary.status === 'completed' ? <CheckCircle2 size={13} aria-hidden="true" /> : <ServerCrash size={13} aria-hidden="true" />}
              Backend status: {state.summary.status}
            </span>
            <span className={`badge ${state.summary.enable_trsm ? 'badge-review' : 'badge-quarantine'}`} style={{ fontSize: '12px' }}>
              {state.summary.enable_trsm ? <Shield size={13} aria-hidden="true" /> : <ShieldOff size={13} aria-hidden="true" />}
              {state.summary.enable_trsm ? 'TRSM protected' : 'Baseline (no TRSM)'}
            </span>
          </div>

          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>run {state.summary.run_id}</div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
            <Stat label="Messages" value={state.summary.total_messages} />
            <Stat label="Tool calls" value={state.summary.total_tool_calls} />
            <Stat label="Blocked" value={state.summary.blocked_actions} />
            <Stat label="Duration" value={formatMs(state.timing.durationMs)} />
          </div>
          {state.timing.startedAt && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
              <Clock size={12} aria-hidden="true" />
              {formatEventTime(state.timing.startedAt)} → {state.timing.endedAt ? formatEventTime(state.timing.endedAt) : 'no end event'}
            </div>
          )}

          {state.stale && <Notice tone="warn">The canvas changed after this run, so node and route results are hidden from the canvas. Execute again to see results for the current workflow.</Notice>}
          {state.eventsError && <Notice tone="error">Audit events could not be loaded, so per-agent results are unavailable. {state.eventsError}</Notice>}
          {state.metricsError && <Notice tone="warn">Metrics are unavailable for this run. {state.metricsError}</Notice>}

          {state.nodeStates && (
            <div>
              <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Agents in this run</div>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Derived from audit events: the backend does not report per-agent status directly.
              </p>
              <ul aria-label="Agents in this run" style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {Object.entries(state.nodeStates).map(([id, s]) => (
                  <li key={id} className="well" style={{ background: '#ffffff', padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={id}>
                        {id}
                      </span>
                      {s.eventCount > 0 && (
                        <button type="button" className="btn btn-secondary" style={{ minHeight: 28, padding: '2px 8px', fontSize: '12px', flexShrink: 0 }} onClick={() => onViewAgentEvents(id)} aria-label={`View trace events for ${id}`}>
                          <ListFilter size={12} aria-hidden="true" /> {s.eventCount} events
                        </button>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
                      <TrsmNodeGuardBadge nodeId={id} status={s.status} />
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }} title={s.firstAt ? `first ${s.firstAt} / last ${s.lastAt}` : undefined}>
                        {s.eventCount === 0 ? 'no events' : `active ${formatMs(s.spanMs)}`}
                      </span>
                    </div>
                    {s.reasons.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {s.reasons.map((r) => (
                          <span key={r} className="badge badge-block" style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, wordBreak: 'break-all' }}>{r}</span>
                        ))}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  );
};
