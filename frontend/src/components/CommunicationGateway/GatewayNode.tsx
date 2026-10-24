import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { ShieldCheck, Network, Lock } from 'lucide-react';

export interface GatewayNodeData {
  totalMediated?: number;
  totalBlocked?: number;
  policyVersion?: string;
  status?: string;
}

export const GatewayNode: React.FC<NodeProps> = ({ data }) => {
  const nodeData = (data as unknown as GatewayNodeData) || {};
  const {
    totalMediated = 0,
    totalBlocked = 0,
    policyVersion = '1.0.0',
    status = 'active',
  } = nodeData;

  return (
    <div
      className="glass-panel"
      style={{
        padding: '16px 20px',
        width: '290px',
        border: '1px solid rgba(129, 140, 248, 0.6)',
        background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)',
        boxShadow: '0 0 30px rgba(99, 102, 241, 0.35)',
        position: 'relative',
      }}
    >
      {/* Target Handles (Left and Top) */}
      <Handle
        type="target"
        position={Position.Left}
        id="in-left"
        style={{ background: '#818cf8', width: '10px', height: '10px' }}
      />
      <Handle
        type="target"
        position={Position.Top}
        id="in-top"
        style={{ background: '#818cf8', width: '10px', height: '10px' }}
      />

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
        <div
          style={{
            padding: '8px',
            borderRadius: '10px',
            background: 'rgba(99, 102, 241, 0.35)',
            color: '#818cf8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Network size={20} />
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '14px', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>TRSM Gateway</span>
            <ShieldCheck size={14} color="#10b981" />
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8' }}>Central Backend Mediation</div>
        </div>
      </div>

      <p style={{ fontSize: '11px', color: '#cbd5e1', marginBottom: '10px', lineHeight: '1.4' }}>
        Mandatory policy inspection point. Inter-agent messages are authorized before delivery.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '11px', background: 'rgba(15, 23, 42, 0.6)', padding: '6px 8px', borderRadius: '6px', marginBottom: '8px' }}>
        <div>
          <span style={{ color: '#64748b' }}>Messages: </span>
          <span style={{ color: '#38bdf8', fontWeight: 600 }}>{totalMediated}</span>
        </div>
        <div>
          <span style={{ color: '#64748b' }}>Blocked: </span>
          <span style={{ color: totalBlocked > 0 ? '#f43f5e' : '#10b981', fontWeight: 600 }}>{totalBlocked}</span>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', borderTop: '1px solid #334155', paddingTop: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ color: '#64748b' }}>Status: </span>
          <span style={{ color: status === 'active' ? '#10b981' : '#f59e0b', fontWeight: 600 }}>
            {status === 'active' ? 'Enforcing' : status}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#818cf8' }}>
          <Lock size={11} />
          <span>Policy v{policyVersion}</span>
        </div>
      </div>

      {/* Source Handles (Right and Bottom) */}
      <Handle
        type="source"
        position={Position.Right}
        id="out-right"
        style={{ background: '#38bdf8', width: '10px', height: '10px' }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="out-bottom"
        style={{ background: '#38bdf8', width: '10px', height: '10px' }}
      />
    </div>
  );
};
