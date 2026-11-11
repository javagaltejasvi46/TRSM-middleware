import React from 'react';
import { Handle, Position, type Node, type NodeProps } from '@xyflow/react';
import { Bot, Flag, Timer } from 'lucide-react';
import { TrsmNodeGuardBadge } from '../TrsmNodeGuardBadge/TrsmNodeGuardBadge';
import { AgentNodeConfig, AgentStatus } from '../../types';
import { ROLE_LABELS } from '../../lib/workflowGraph';

export type AgentFlowNode = Node<
  { config: AgentNodeConfig; isEntry: boolean; status: AgentStatus; hasIncoming: boolean; hasOutgoing: boolean },
  'agent'
>;

/** Border tint per backend-reported status; the badge text carries the meaning too. */
const STATUS_BORDER: Partial<Record<AgentStatus, string>> = {
  completed: '#a7f3d0',
  blocked: '#fca5a5',
  failed: '#fca5a5',
  quarantined: '#fcd34d',
  review_required: '#c4b5fd',
};

/** Ports are filled when a route is attached and hollow when not (shape, not just colour). */
const portStyle = (connected: boolean): React.CSSProperties => ({
  width: 14,
  height: 14,
  background: connected ? 'var(--accent-primary)' : '#ffffff',
  border: `2px solid ${connected ? '#ffffff' : 'var(--input-border)'}`,
  boxShadow: connected ? '0 0 0 1px var(--accent-primary), 0 1px 3px rgba(30, 27, 75, 0.3)' : '0 1px 2px rgba(30, 27, 75, 0.15)',
});

const Param: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '10px', fontSize: '12px' }}>
    <dt style={{ color: 'var(--text-secondary)', flexShrink: 0, paddingTop: 1 }}>{label}</dt>
    <dd style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'flex-end', gap: '4px', minWidth: 0 }}>{children}</dd>
  </div>
);

const Pill: React.FC<{ children: React.ReactNode; muted?: boolean }> = ({ children, muted }) => (
  <span
    style={{
      fontFamily: 'var(--font-mono)',
      fontSize: '11px',
      fontWeight: 500,
      padding: '1px 6px',
      borderRadius: 6,
      background: muted ? 'transparent' : 'var(--surface-sunken)',
      border: `1px solid ${muted ? 'transparent' : 'var(--border-color)'}`,
      color: muted ? 'var(--text-muted)' : 'var(--text-primary)',
      maxWidth: 150,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
    }}
  >
    {children}
  </span>
);

export const AgentNode: React.FC<NodeProps<AgentFlowNode>> = ({ data, selected }) => {
  const { config, isEntry, status, hasIncoming, hasOutgoing } = data;
  const running = status === 'running';
  const tint = STATUS_BORDER[status];
  const list = (items: string[]) => (items.length ? items.map((x) => <Pill key={x}>{x}</Pill>) : <Pill muted>none</Pill>);

  return (
    <div className={`agent-node${running ? ' is-running' : ''}`} data-status={status} style={{ position: 'relative', width: '264px' }}>
      {running && <span aria-hidden="true" className="agent-glow" />}
      <div
        className={`surface surface-lift${selected ? ' is-selected' : ''}`}
        style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden', ...(tint && !selected ? { borderColor: tint } : {}) }}
      >
        {running && <span aria-hidden="true" className="agent-sweep" />}

        <header style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '12px 14px 10px' }}>
          <span className="icon-chip" style={{ padding: 8 }}>
            <Bot size={18} aria-hidden="true" />
          </span>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <h4 style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {config.name || '(unnamed)'}
              </h4>
              {isEntry && (
                <span title="Entry node: receives the initial task" style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', fontSize: '11px', fontWeight: 700, color: 'var(--warn-text)', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 6, padding: '0 5px', whiteSpace: 'nowrap' }}>
                  <Flag size={11} aria-hidden="true" /> Entry
                </span>
              )}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {config.node_id} · {ROLE_LABELS[config.role] ?? config.role}
            </div>
          </div>
        </header>

        <div style={{ padding: '0 14px 10px' }}>
          <TrsmNodeGuardBadge nodeId={config.node_id} status={status} />
        </div>

        <dl style={{ display: 'flex', flexDirection: 'column', gap: '6px', padding: '0 14px 12px' }}>
          <Param label="Model">
            <Pill>{config.model || 'mock'}</Pill>
          </Param>
          <Param label="Peers">{list(config.allowed_peers)}</Param>
          <Param label="Tools">{list(config.allowed_tools)}</Param>
        </dl>

        <footer
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            borderTop: '1px solid var(--border-color)',
            background: 'var(--surface-sunken)',
            fontSize: '11px',
            color: 'var(--text-secondary)',
          }}
        >
          <Timer size={12} aria-hidden="true" />
          {config.timeout_seconds}s timeout · max {config.call_limit} calls
        </footer>
      </div>

      <Handle type="target" position={Position.Left} style={{ ...portStyle(hasIncoming), top: 34 }} aria-label={`Incoming routes to ${config.node_id}${hasIncoming ? '' : ' (none)'}`} />
      <Handle type="source" position={Position.Right} style={{ ...portStyle(hasOutgoing), top: 34 }} aria-label={`Add a route from ${config.node_id}`} />
    </div>
  );
};
