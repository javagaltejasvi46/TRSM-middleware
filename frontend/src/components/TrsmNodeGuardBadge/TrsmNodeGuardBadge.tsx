import React from 'react';
import { ShieldCheck, ShieldAlert } from 'lucide-react';

interface TrsmNodeGuardBadgeProps {
  nodeId: string;
  status?: string;
  isEnforced?: boolean;
}

export const TrsmNodeGuardBadge: React.FC<TrsmNodeGuardBadgeProps> = ({
  status = 'active',
  isEnforced = true,
}) => {
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '3px 8px',
        borderRadius: '9999px',
        fontSize: '11px',
        fontWeight: 600,
        letterSpacing: '0.04em',
        textTransform: 'uppercase',
        background: isEnforced ? 'rgba(99, 102, 241, 0.15)' : 'rgba(100, 116, 139, 0.2)',
        color: isEnforced ? '#818cf8' : '#94a3b8',
        border: `1px solid ${isEnforced ? 'rgba(99, 102, 241, 0.4)' : '#475569'}`,
        boxShadow: isEnforced ? '0 0 10px rgba(99, 102, 241, 0.25)' : 'none',
      }}
    >
      {isEnforced ? <ShieldCheck size={13} /> : <ShieldAlert size={13} />}
      <span>TRSM Guard</span>
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          background: isEnforced ? '#10b981' : '#f59e0b',
        }}
      />
    </div>
  );
};
