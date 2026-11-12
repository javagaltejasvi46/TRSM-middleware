import React from 'react';
import { Play, Shield, ShieldOff, Loader2 } from 'lucide-react';
import { PRELOADED_WORKFLOWS } from '../../lib/preloadedWorkflows';

interface RunControlsProps {
  isRunning: boolean;
  enableTrsm: boolean;
  task: string;
  onTaskChange: (task: string) => void;
  selectedWorkflowId?: string;
  onSelectWorkflowId?: (id: string) => void;
  onStartRun: (task: string, enableTrsm: boolean) => void;
  /** When set, running is disabled and this explains why (a browser pre-check, not a policy decision). */
  blockedReason?: string | null;
}

export const RunControls: React.FC<RunControlsProps> = ({
  isRunning,
  enableTrsm,
  task,
  onTaskChange,
  selectedWorkflowId,
  onSelectWorkflowId,
  onStartRun,
  blockedReason,
}) => {
  return (
    <div className="surface" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>Execution Controls</h3>
        {/* Mode indicator (the actual toggle button has been shifted onto the TRSM Gateway node on the canvas) */}
        <span
          className={`badge ${enableTrsm ? 'badge-allow' : 'badge-block'}`}
          style={{ minHeight: '26px', padding: '2px 8px', fontSize: '11px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
          title="Current enforcement mode. Toggle this using the TRSM button on the Central Gateway node on the canvas."
        >
          {enableTrsm ? <Shield size={12} aria-hidden="true" /> : <ShieldOff size={12} aria-hidden="true" />}
          <span>{enableTrsm ? 'TRSM Protected' : 'Baseline (no TRSM)'}</span>
        </span>
      </div>

      <div className="field">
        <label className="field-label" htmlFor="run-preset">Preloaded attack workflow</label>
        <select
          id="run-preset"
          className="field-input"
          value={selectedWorkflowId ?? ''}
          onChange={(e) => onSelectWorkflowId?.(e.target.value)}
        >
          {PRELOADED_WORKFLOWS.map((sc) => (
            <option key={sc.id} value={sc.id}>
              {sc.name}
            </option>
          ))}
          {selectedWorkflowId && !PRELOADED_WORKFLOWS.some((sc) => sc.id === selectedWorkflowId) && (
            <option value="custom">Custom / Modified Workflow</option>
          )}
        </select>
        <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
          Selecting an attack updates both the diagram and instructions automatically.
        </span>
      </div>

      <div className="field">
        <label className="field-label" htmlFor="run-task">Task prompt / attack instruction</label>
        <textarea
          id="run-task"
          className="field-input"
          rows={2}
          value={task}
          onChange={(e) => onTaskChange(e.target.value)}
          style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', resize: 'vertical' }}
        />
      </div>

      <button
        type="button"
        className="btn btn-primary"
        disabled={isRunning || Boolean(blockedReason) || !task.trim()}
        aria-describedby={blockedReason ? 'run-blocked-reason' : undefined}
        onClick={() => onStartRun(task, enableTrsm)}
        style={{ width: '100%', minHeight: '42px' }}
      >
        {isRunning ? <Loader2 size={16} className="animate-spin" aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
        <span>{isRunning ? 'Executing workflow…' : 'Execute Run'}</span>
      </button>
      {blockedReason && (
        <p id="run-blocked-reason" className="field-error" style={{ marginTop: '-4px' }}>
          {blockedReason}
        </p>
      )}
    </div>
  );
};
