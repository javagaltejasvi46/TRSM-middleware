import React from 'react';
import { CircleDashed, ShieldAlert, ShieldCheck, ShieldQuestion, ShieldX } from 'lucide-react';
import { PolicyDecisionEnum } from '../../types';

const MAP: Record<PolicyDecisionEnum, { cls: string; Icon: React.ElementType }> = {
  ALLOW: { cls: 'badge-allow', Icon: ShieldCheck },
  BLOCK: { cls: 'badge-block', Icon: ShieldX },
  QUARANTINE: { cls: 'badge-quarantine', Icon: ShieldAlert },
  REVIEW: { cls: 'badge-review', Icon: ShieldQuestion },
};

/** Policy decision as icon + text; `null` renders an explicit "no decision". */
export const DecisionBadge: React.FC<{ decision: PolicyDecisionEnum | null; noneLabel?: string }> = ({ decision, noneLabel = 'No decision' }) => {
  if (!decision) {
    return (
      <span className="badge" style={{ color: 'var(--text-secondary)', border: '1px dashed var(--border-strong)', background: '#ffffff' }}>
        <CircleDashed size={12} aria-hidden="true" />
        {noneLabel}
      </span>
    );
  }
  const { cls, Icon } = MAP[decision];
  return (
    <span className={`badge ${cls}`}>
      <Icon size={12} aria-hidden="true" />
      {decision}
    </span>
  );
};
