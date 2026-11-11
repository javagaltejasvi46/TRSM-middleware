import React from 'react';
import { ShieldCheck, ShieldAlert, ShieldX, ShieldQuestion, Loader2, CircleDashed } from 'lucide-react';
import type { NodeRunStatus } from '../../lib/runState';

interface TrsmNodeGuardBadgeProps {
  nodeId: string;
  /** Runtime status reported by the backend; 'idle' until a run reports otherwise. */
  status?: NodeRunStatus;
}

const STATUS_DISPLAY: Record<NodeRunStatus, { label: string; color: string; Icon: React.ElementType }> = {
  idle: { label: 'Idle', color: 'var(--text-secondary)', Icon: ShieldCheck },
  running: { label: 'Running', color: 'var(--accent-text)', Icon: Loader2 },
  completed: { label: 'Completed', color: 'var(--status-allow)', Icon: ShieldCheck },
  blocked: { label: 'Blocked', color: 'var(--status-block)', Icon: ShieldX },
  quarantined: { label: 'Quarantined', color: 'var(--status-quarantine)', Icon: ShieldAlert },
  failed: { label: 'Failed', color: 'var(--status-block)', Icon: ShieldX },
  review_required: { label: 'Awaiting review', color: 'var(--status-review)', Icon: ShieldQuestion },
  not_reached: { label: 'Not reached', color: 'var(--text-muted)', Icon: CircleDashed },
};

/**
 * Visual marker that this node's traffic is mediated by TRSM. It displays status
 * reported by the backend; it does not enforce anything itself.
 */
export const TrsmNodeGuardBadge: React.FC<TrsmNodeGuardBadgeProps> = ({ nodeId, status = 'idle' }) => {
  const { label, color, Icon } = STATUS_DISPLAY[status] ?? STATUS_DISPLAY.idle;
  return (
    <div
      role="status"
      aria-label={`TRSM Node Guard for ${nodeId}: ${label}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '3px 8px',
        borderRadius: '9999px',
        fontSize: '11px',
        fontWeight: 600,
        letterSpacing: '0.04em',
        background: 'linear-gradient(180deg, #ffffff 0%, var(--accent-soft) 100%)',
        color: 'var(--accent-text)',
        border: '1px solid var(--border-strong)',
        boxShadow: 'inset 0 1px 0 #ffffff, 0 1px 2px rgba(79, 70, 229, 0.12)',
      }}
    >
      <ShieldCheck size={13} aria-hidden="true" />
      <span style={{ textTransform: 'uppercase' }}>TRSM Guard</span>
      <span aria-hidden="true" style={{ color: 'var(--text-muted)' }}>·</span>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color }}>
        <Icon size={12} aria-hidden="true" />
        {label}
      </span>
    </div>
  );
};
