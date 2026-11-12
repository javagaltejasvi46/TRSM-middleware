import React from 'react';
import { type Node, type NodeProps } from '@xyflow/react';
import { Network, Shield, ShieldOff } from 'lucide-react';

/**
 * Counts come from audit events of the latest run; null means no run data yet.
 * The gateway itself runs in the backend; this node visualizes it and hosts the TRSM enforcement toggle.
 */
export type GatewayFlowNode = Node<
  {
    mediated: number | null;
    blocked: number | null;
    enableTrsm?: boolean;
    onToggleTrsm?: () => void;
  },
  'gateway'
>;

export const GatewayNode: React.FC<NodeProps<GatewayFlowNode>> = ({ data }) => {
  const hasRun = data.mediated !== null;
  const isProtected = data.enableTrsm ?? true;

  return (
    <div
      style={{
        padding: '16px 18px',
        width: '320px',
        borderRadius: 'var(--radius-lg)',
        border: `1px solid ${isProtected ? 'var(--border-strong)' : '#fca5a5'}`,
        background: isProtected
          ? 'linear-gradient(180deg, #ffffff 0%, #eef2ff 100%)'
          : 'linear-gradient(180deg, #ffffff 0%, #fff1f2 100%)',
        // A raised plinth: lit top edge, a solid slab underneath, then soft ambient shadow.
        boxShadow: isProtected
          ? 'inset 0 1px 0 #ffffff, inset 0 -2px 0 rgba(79, 70, 229, 0.08), 0 6px 0 -1px #c7d2fe, 0 14px 28px rgba(79, 70, 229, 0.18), 0 30px 60px -20px rgba(30, 27, 75, 0.25)'
          : 'inset 0 1px 0 #ffffff, inset 0 -2px 0 rgba(239, 68, 68, 0.08), 0 6px 0 -1px #fecaca, 0 14px 28px rgba(239, 68, 68, 0.18), 0 30px 60px -20px rgba(69, 10, 10, 0.25)',
        pointerEvents: 'all',
        transition: 'all 0.2s ease',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            className="icon-chip"
            style={{
              padding: '9px',
              color: '#ffffff',
              background: isProtected
                ? 'linear-gradient(180deg, #6366f1 0%, #4338ca 100%)'
                : 'linear-gradient(180deg, #ef4444 0%, #b91c1c 100%)',
              borderColor: isProtected ? '#4338ca' : '#b91c1c',
            }}
          >
            <Network size={20} aria-hidden="true" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-primary)' }}>TRSM Gateway</div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Backend mediation point</div>
          </div>
        </div>

        {/* Shifted TRSM ON/OFF button directly on the gateway node */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            data.onToggleTrsm?.();
          }}
          aria-pressed={isProtected}
          aria-label={isProtected ? 'TRSM is ON (Protected mode). Click to toggle OFF.' : 'TRSM is OFF (Baseline mode). Click to toggle ON.'}
          className={`nodrag nopan badge ${isProtected ? 'badge-allow' : 'badge-block'}`}
          style={{
            cursor: 'pointer',
            minHeight: '30px',
            padding: '4px 10px',
            fontSize: '11px',
            fontWeight: 700,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '5px',
            border: '1px solid currentColor',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            userSelect: 'none',
          }}
          title={isProtected ? 'TRSM is ON (Protected mode). Click to toggle OFF.' : 'TRSM is OFF (Baseline mode). Click to toggle ON.'}
        >
          {isProtected ? <Shield size={13} aria-hidden="true" /> : <ShieldOff size={13} aria-hidden="true" />}
          <span>{isProtected ? 'TRSM: ON' : 'TRSM: OFF'}</span>
        </button>
      </div>

      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px', lineHeight: 1.4 }}>
        {isProtected
          ? 'Every inter-agent message and tool call is intercepted and verified by the TRSM Policy Engine.'
          : 'TRSM enforcement is bypassed. Inter-agent messages and tool calls execute directly without mediation (Baseline mode).'}
      </p>

      <div className="well" style={{ fontSize: '12px', padding: '8px 10px', color: 'var(--text-secondary)' }}>
        {hasRun ? (
          <span>
            Last run: <strong style={{ color: 'var(--text-primary)' }}>{data.mediated}</strong> message decisions,{' '}
            <strong style={{ color: 'var(--text-primary)' }}>{data.blocked}</strong> blocked or quarantined
          </span>
        ) : (
          <span>No run data yet. Decisions appear after a run.</span>
        )}
      </div>
    </div>
  );
};
