import React, { useId, useMemo, useState } from 'react';
import { AlertCircle, Flag, Trash2, X } from 'lucide-react';
import { AgentNodeConfig, AgentRole } from '../../types';
import { AGENT_ROLES, KNOWN_TOOLS, LIMITS, ROLE_LABELS } from '../../lib/workflowGraph';
import { validateNodeFields } from '../../lib/workflowChecks';

export interface NodeConfigPanelProps {
  node: AgentNodeConfig;
  /** IDs of every other node in the workflow. */
  otherNodeIds: string[];
  isEntry: boolean;
  onApply: (next: AgentNodeConfig) => void;
  onDelete: () => void;
  onSetEntry: () => void;
}

type Draft = Omit<AgentNodeConfig, 'timeout_seconds' | 'call_limit'> & { timeout_seconds: string; call_limit: string };

const toDraft = (n: AgentNodeConfig): Draft => ({ ...n, timeout_seconds: String(n.timeout_seconds), call_limit: String(n.call_limit) });
const parseIntStrict = (s: string) => (/^-?\d+$/.test(s.trim()) ? Number(s.trim()) : NaN);
const fromDraft = (d: Draft): AgentNodeConfig => ({
  ...d,
  node_id: d.node_id.trim(),
  timeout_seconds: parseIntStrict(d.timeout_seconds),
  call_limit: parseIntStrict(d.call_limit),
});

/**
 * Edits one agent's configuration. Changes are held in a draft until Apply, then
 * the parent updates the workflow (and edges, since they follow allowed_peers).
 * Field rules mirror backend/app/schemas/agent.py; the backend re-validates.
 */
export const NodeConfigPanel: React.FC<NodeConfigPanelProps> = ({ node, otherNodeIds, isEntry, onApply, onDelete, onSetEntry }) => {
  const uid = useId();
  const [draft, setDraft] = useState<Draft>(() => toDraft(node));
  const [toolInput, setToolInput] = useState('');
  const candidate = useMemo(() => fromDraft(draft), [draft]);
  const errors = useMemo(() => validateNodeFields(candidate, otherNodeIds), [candidate, otherNodeIds]);
  const hasErrors = Object.keys(errors).length > 0;
  const dirty = JSON.stringify(candidate) !== JSON.stringify(node);

  const set = <K extends keyof Draft>(key: K, value: Draft[K]) => setDraft((d) => ({ ...d, [key]: value }));
  const fid = (name: string) => `${uid}-${name}`;
  const errProps = (name: keyof typeof errors) =>
    errors[name] ? { 'aria-invalid': true as const, 'aria-describedby': fid(`${name}-error`) } : { 'aria-invalid': false as const };
  const errorText = (name: keyof typeof errors) =>
    errors[name] ? (
      <span id={fid(`${name}-error`)} className="field-error">
        <AlertCircle size={12} aria-hidden="true" />
        {errors[name]}
      </span>
    ) : null;

  const togglePeer = (peer: string, on: boolean) =>
    set('allowed_peers', on ? [...draft.allowed_peers, peer] : draft.allowed_peers.filter((p) => p !== peer));
  const danglingPeers = draft.allowed_peers.filter((p) => !otherNodeIds.includes(p));

  const addTool = () => {
    const t = toolInput.trim();
    if (t && !draft.allowed_tools.includes(t)) set('allowed_tools', [...draft.allowed_tools, t]);
    setToolInput('');
  };

  return (
    <form
      className="surface"
      style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}
      aria-labelledby={fid('title')}
      onSubmit={(e) => {
        e.preventDefault();
        if (!hasErrors) onApply(candidate);
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
        <h2 id={fid('title')} style={{ fontSize: '14px', fontWeight: 600 }}>
          Configure <span style={{ fontFamily: 'var(--font-mono)' }}>{node.node_id}</span>
        </h2>
        {isEntry ? (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--warn-text)' }}>
            <Flag size={12} aria-hidden="true" /> Entry node
          </span>
        ) : (
          <button type="button" className="btn btn-secondary" onClick={onSetEntry}>
            <Flag size={14} aria-hidden="true" /> Set as entry
          </button>
        )}
      </div>

      <div className="field">
        <label className="field-label" htmlFor={fid('node_id')}>Node ID</label>
        <input id={fid('node_id')} className="field-input" value={draft.node_id} onChange={(e) => set('node_id', e.target.value)} {...errProps('node_id')} />
        <span className="field-help">Renaming updates routes and peer lists that point to this node.</span>
        {errorText('node_id')}
      </div>

      <div className="field">
        <label className="field-label" htmlFor={fid('name')}>Display name</label>
        <input id={fid('name')} className="field-input" value={draft.name} onChange={(e) => set('name', e.target.value)} {...errProps('name')} />
        {errorText('name')}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <div className="field">
          <label className="field-label" htmlFor={fid('role')}>Role</label>
          <select id={fid('role')} className="field-input" value={draft.role} onChange={(e) => set('role', e.target.value as AgentRole)} {...errProps('role')}>
            {AGENT_ROLES.map((r) => (
              <option key={r} value={r}>{ROLE_LABELS[r]}</option>
            ))}
          </select>
          {errorText('role')}
        </div>
        <div className="field">
          <label className="field-label" htmlFor={fid('model')}>Model</label>
          <input id={fid('model')} className="field-input" value={draft.model} onChange={(e) => set('model', e.target.value)} placeholder="mock" />
          <span className="field-help">e.g. mock, llama3:8b</span>
        </div>
      </div>

      <div className="field">
        <label className="field-label" htmlFor={fid('instructions')}>Task / instructions</label>
        <textarea id={fid('instructions')} className="field-input" rows={3} value={draft.instructions} onChange={(e) => set('instructions', e.target.value)} />
      </div>

      <fieldset className="field" style={{ border: 'none' }}>
        <legend className="field-label" style={{ marginBottom: '4px' }}>Allowed peers</legend>
        <span className="field-help" style={{ marginBottom: '4px' }}>Each peer is drawn as a route on the canvas. The backend Policy Engine checks this list at run time.</span>
        {otherNodeIds.length === 0 && <span className="field-help">No other agents on the canvas yet.</span>}
        {otherNodeIds.map((peer) => (
          <label key={peer} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', minHeight: '28px', cursor: 'pointer' }}>
            <input type="checkbox" checked={draft.allowed_peers.includes(peer)} onChange={(e) => togglePeer(peer, e.target.checked)} />
            <span style={{ fontFamily: 'var(--font-mono)' }}>{peer}</span>
          </label>
        ))}
        {danglingPeers.map((peer) => (
          <div key={peer} className="field-error" style={{ justifyContent: 'space-between' }}>
            <span>
              <AlertCircle size={12} aria-hidden="true" /> "{peer}" is not in this workflow
            </span>
            <button type="button" className="btn btn-secondary" onClick={() => togglePeer(peer, false)} aria-label={`Remove peer ${peer}`}>
              <X size={12} aria-hidden="true" /> Remove
            </button>
          </div>
        ))}
      </fieldset>

      <div className="field">
        <label className="field-label" htmlFor={fid('tools')}>Allowed tools</label>
        <ul style={{ listStyle: 'none', display: 'flex', flexWrap: 'wrap', gap: '6px' }} aria-label="Current tools">
          {draft.allowed_tools.map((t) => (
            <li key={t} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '2px 4px 2px 8px', borderRadius: '9999px', border: '1px solid var(--border-strong)', background: 'var(--accent-soft)', color: 'var(--accent-text)', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
              {t}
              {!KNOWN_TOOLS.includes(t) && <span style={{ color: 'var(--warn-text)', fontFamily: 'var(--font-sans)' }}>(unregistered)</span>}
              <button
                type="button"
                onClick={() => set('allowed_tools', draft.allowed_tools.filter((x) => x !== t))}
                aria-label={`Remove tool ${t}`}
                style={{ display: 'inline-flex', padding: '4px', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', borderRadius: '9999px' }}
              >
                <X size={12} aria-hidden="true" />
              </button>
            </li>
          ))}
          {draft.allowed_tools.length === 0 && <li className="field-help">None</li>}
        </ul>
        <div style={{ display: 'flex', gap: '6px' }}>
          <input
            id={fid('tools')}
            className="field-input"
            list={fid('tools-list')}
            value={toolInput}
            onChange={(e) => setToolInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                addTool();
              }
            }}
            placeholder="customer_db"
          />
          <datalist id={fid('tools-list')}>
            {KNOWN_TOOLS.filter((t) => !draft.allowed_tools.includes(t)).map((t) => (
              <option key={t} value={t} />
            ))}
          </datalist>
          <button type="button" className="btn btn-secondary" onClick={addTool} disabled={!toolInput.trim()}>Add</button>
        </div>
        <span className="field-help">Registered: {KNOWN_TOOLS.join(', ')}. Unregistered tools are blocked by the backend.</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <div className="field">
          <label className="field-label" htmlFor={fid('timeout_seconds')}>Timeout (s)</label>
          <input id={fid('timeout_seconds')} className="field-input" inputMode="numeric" value={draft.timeout_seconds} onChange={(e) => set('timeout_seconds', e.target.value)} {...errProps('timeout_seconds')} />
          <span className="field-help">{LIMITS.timeout_seconds.min}–{LIMITS.timeout_seconds.max}</span>
          {errorText('timeout_seconds')}
        </div>
        <div className="field">
          <label className="field-label" htmlFor={fid('call_limit')}>Call limit</label>
          <input id={fid('call_limit')} className="field-input" inputMode="numeric" value={draft.call_limit} onChange={(e) => set('call_limit', e.target.value)} {...errProps('call_limit')} />
          <span className="field-help">{LIMITS.call_limit.min}–{LIMITS.call_limit.max}</span>
          {errorText('call_limit')}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', justifyContent: 'space-between', borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
        <button type="button" className="btn btn-danger" onClick={onDelete}>
          <Trash2 size={14} aria-hidden="true" /> Delete node
        </button>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button type="button" className="btn btn-secondary" disabled={!dirty} onClick={() => setDraft(toDraft(node))}>Reset</button>
          <button type="submit" className="btn btn-primary" disabled={!dirty || hasErrors}>Apply</button>
        </div>
      </div>
      {dirty && <span className="field-help" role="status">{hasErrors ? 'Fix the highlighted fields to apply.' : 'Unapplied changes.'}</span>}
    </form>
  );
};
