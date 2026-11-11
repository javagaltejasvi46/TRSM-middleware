import React, { useRef, useState } from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Download, Loader2, ServerCrash, ShieldCheck, Upload } from 'lucide-react';
import { WorkflowConfig, WorkflowValidationResult } from '../../types';
import { exportWorkflowJson, importWorkflowJson, toWorkflowConfig } from '../../lib/workflowGraph';
import { PreCheckResult } from '../../lib/workflowChecks';
import { workflowsApi } from '../../api/workflows';

interface WorkflowToolbarProps {
  workflow: WorkflowConfig;
  preChecks: PreCheckResult;
  onRename: (name: string) => void;
  onImport: (wf: WorkflowConfig) => void;
}

type BackendState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'result'; result: WorkflowValidationResult; checked: string }
  | { kind: 'error'; message: string };

export const WorkflowToolbar: React.FC<WorkflowToolbarProps> = ({ workflow, preChecks, onRename, onImport }) => {
  const fileRef = useRef<HTMLInputElement>(null);
  const [backend, setBackend] = useState<BackendState>({ kind: 'idle' });
  const [importMsg, setImportMsg] = useState<{ ok: boolean; lines: string[] } | null>(null);
  const currentJson = exportWorkflowJson(workflow);
  const stale = backend.kind === 'result' && backend.checked !== currentJson;

  const exportFile = () => {
    const blob = new Blob([currentJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(workflow.name || 'workflow').replace(/[^a-z0-9_-]+/gi, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const importFile = async (file: File) => {
    const res = importWorkflowJson(await file.text());
    if (res.ok) {
      onImport(res.workflow);
      setBackend({ kind: 'idle' });
      setImportMsg({ ok: true, lines: [`Imported "${res.workflow.name}" (${res.workflow.nodes.length} nodes).`, ...res.notices] });
    } else {
      setImportMsg({ ok: false, lines: ['Import rejected; the canvas was not changed.', ...res.errors] });
    }
  };

  const validate = async () => {
    setBackend({ kind: 'loading' });
    try {
      const result = await workflowsApi.validate(toWorkflowConfig(workflow));
      setBackend({ kind: 'result', result, checked: currentJson });
    } catch (e) {
      setBackend({ kind: 'error', message: (e as Error).message });
    }
  };

  return (
    <div className="surface" style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-end', gap: '10px' }}>
        <div className="field" style={{ flex: '1 1 240px' }}>
          <label className="field-label" htmlFor="workflow-name">Workflow name</label>
          <input id="workflow-name" className="field-input" value={workflow.name} onChange={(e) => onRename(e.target.value)} />
        </div>
        <button type="button" className="btn btn-secondary" onClick={exportFile}>
          <Download size={14} aria-hidden="true" /> Export JSON
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => fileRef.current?.click()}>
          <Upload size={14} aria-hidden="true" /> Import JSON
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="application/json,.json"
          hidden
          aria-hidden="true"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) importFile(f);
            e.target.value = '';
          }}
        />
        <button type="button" className="btn btn-primary" onClick={validate} disabled={backend.kind === 'loading'}>
          {backend.kind === 'loading' ? <Loader2 size={14} className="animate-spin" aria-hidden="true" /> : <ShieldCheck size={14} aria-hidden="true" />}
          Validate with backend
        </button>
      </div>

      {importMsg && (
        <MessageList tone={importMsg.ok ? (importMsg.lines.length > 1 ? 'warn' : 'ok') : 'error'} lines={importMsg.lines} onDismiss={() => setImportMsg(null)} />
      )}

      <section aria-labelledby="prechecks-title" style={{ fontSize: '12px' }}>
        <h3 id="prechecks-title" style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Local pre-checks <span style={{ fontWeight: 400 }}>(in the browser only, not a policy decision)</span>
        </h3>
        {preChecks.errors.length === 0 && preChecks.warnings.length === 0 ? (
          <p style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--ok-text)', marginTop: '4px' }}>
            <CheckCircle2 size={13} aria-hidden="true" /> No issues found
          </p>
        ) : (
          <ul style={{ listStyle: 'none', marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
            {preChecks.errors.map((m) => (
              <li key={`e-${m}`} style={{ display: 'flex', gap: '6px', color: 'var(--error-text)' }}><AlertCircle size={13} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} /> <span><strong>Error:</strong> {m}</span></li>
            ))}
            {preChecks.warnings.map((m) => (
              <li key={`w-${m}`} style={{ display: 'flex', gap: '6px', color: 'var(--warn-text)' }}><AlertTriangle size={13} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} /> <span><strong>Warning:</strong> {m}</span></li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="backend-validation-title" aria-live="polite" style={{ fontSize: '12px' }}>
        <h3 id="backend-validation-title" style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Backend validation <span style={{ fontWeight: 400 }}>(POST /api/workflows/validate)</span>
        </h3>
        {backend.kind === 'idle' && <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Not validated yet.</p>}
        {backend.kind === 'loading' && <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Validating…</p>}
        {backend.kind === 'error' && (
          <p style={{ display: 'flex', gap: '6px', color: 'var(--error-text)', marginTop: '4px' }}>
            <ServerCrash size={13} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} />
            <span><strong>Not validated:</strong> could not reach the backend or it returned an error. {backend.message}</span>
          </p>
        )}
        {backend.kind === 'result' && (
          <div style={{ marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <p style={{ display: 'flex', gap: '6px', alignItems: 'center', color: backend.result.is_valid ? 'var(--ok-text)' : 'var(--error-text)' }}>
              {backend.result.is_valid ? <CheckCircle2 size={13} aria-hidden="true" /> : <AlertCircle size={13} aria-hidden="true" />}
              <strong>{backend.result.is_valid ? 'Valid' : 'Invalid'}</strong>
              {stale && <span style={{ color: 'var(--warn-text)', fontWeight: 400 }}>· the workflow changed since this check; validate again</span>}
            </p>
            {backend.result.errors.map((m) => <p key={`be-${m}`} style={{ color: 'var(--error-text)' }}>Error: {m}</p>)}
            {backend.result.warnings.map((m) => <p key={`bw-${m}`} style={{ color: 'var(--warn-text)' }}>Warning: {m}</p>)}
          </div>
        )}
      </section>
    </div>
  );
};

const MessageList: React.FC<{ tone: 'ok' | 'warn' | 'error'; lines: string[]; onDismiss: () => void }> = ({ tone, lines, onDismiss }) => {
  const cls = tone === 'ok' ? 'badge-allow' : tone === 'warn' ? 'badge-quarantine' : 'badge-block';
  const Icon = tone === 'ok' ? CheckCircle2 : tone === 'warn' ? AlertTriangle : AlertCircle;
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={cls} style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', fontSize: '12px', fontWeight: 500, borderRadius: '10px', padding: '8px 10px' }}>
      <div style={{ display: 'flex', gap: '6px' }}>
        <Icon size={13} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} />
        <ul style={{ listStyle: 'none' }}>{lines.map((l, i) => <li key={i}>{l}</li>)}</ul>
      </div>
      <button type="button" className="btn btn-secondary" onClick={onDismiss} style={{ minHeight: 28 }}>Dismiss</button>
    </div>
  );
};
