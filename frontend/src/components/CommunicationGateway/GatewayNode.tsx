import React from 'react';
import { type Node, type NodeProps } from '@xyflow/react';
import { Network } from 'lucide-react';

/**
 * Counts come from audit events of the latest run; null means no run data yet.
 * The gateway itself runs in the backend; this node only visualizes it.
 */
export type GatewayFlowNode = Node<{ mediated: number | null; blocked: number | null }, 'gateway'>;

export const GatewayNode: React.FC<NodeProps<GatewayFlowNode>> = ({ data }) => {
  const hasRun = data.mediated !== null;
  return (
    <div
      style={{
        padding: '16px 18px',
        width: '300px',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-strong)',
        background: 'linear-gradient(180deg, #ffffff 0%, #eef2ff 100%)',
        // A raised plinth: lit top edge, a solid slab underneath, then soft ambient shadow.
        boxShadow:
          'inset 0 1px 0 #ffffff, inset 0 -2px 0 rgba(79, 70, 229, 0.08), 0 6px 0 -1px #c7d2fe, 0 14px 28px rgba(79, 70, 229, 0.18), 0 30px 60px -20px rgba(30, 27, 75, 0.25)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
        <div className="icon-chip" style={{ padding: '9px', color: '#ffffff', background: 'linear-gradient(180deg, #6366f1 0%, #4338ca 100%)', borderColor: '#4338ca' }}>
          <Network size={20} aria-hidden="true" />
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>TRSM Communication Gateway</div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Backend mediation point</div>
        </div>
      </div>

      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px', lineHeight: 1.5 }}>
        Every route drawn on this canvas is a configured path, not a permission. Each message is checked by the backend Policy Engine at run time.
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
