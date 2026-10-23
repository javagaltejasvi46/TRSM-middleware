import React from 'react';
import { ShieldCheck, Network, Lock } from 'lucide-react';

interface GatewayNodeProps {
  totalMediated?: number;
  totalBlocked?: number;
}

export const GatewayNode: React.FC<GatewayNodeProps> = ({
  totalMediated = 0,
  totalBlocked = 0,
}) => {
  return (
    <div
      className="glass-panel"
      style={{
        padding: '16px 20px',
        width: '300px',
        border: '1px solid rgba(129, 140, 248, 0.5)',
        background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)',
        boxShadow: '0 0 25px rgba(99, 102, 241, 0.25)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
        <div
          style={{
            padding: '8px',
            borderRadius: '10px',
            background: 'rgba(99, 102, 241, 0.3)',
            color: '#818cf8',
          }}
        >
          <Network size={20} />
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '14px', color: '#f8fafc' }}>
            TRSM Communication Gateway
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8' }}>Central Backend Mediation</div>
        </div>
      </div>

      <p style={{ fontSize: '12px', color: '#cbd5e1', marginBottom: '12px', lineHeight: '1.4' }}>
        Mandatory policy inspection point. All inter-agent message envelopes are validated, threat-scanned, and authorized here.
      </p>

      <div style={{ display: 'flex', gap: '12px', fontSize: '12px', borderTop: '1px solid #334155', paddingTop: '8px' }}>
        <div>
          <span style={{ color: '#64748b' }}>Status: </span>
          <span style={{ color: '#10b981', fontWeight: 600 }}>Active (Fail-Closed)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#f43f5e' }}>
          <Lock size={12} />
          <span>Policy v1.0</span>
        </div>
      </div>
    </div>
  );
};
