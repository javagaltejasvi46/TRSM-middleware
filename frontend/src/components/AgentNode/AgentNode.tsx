import React from 'react';
import { Bot, Wrench, Users } from 'lucide-react';
import { TrsmNodeGuardBadge } from '../TrsmNodeGuardBadge/TrsmNodeGuardBadge';
import { AgentRole } from '../../types';

interface AgentNodeProps {
  id: string;
  name: string;
  role: AgentRole;
  model: string;
  allowedPeers: string[];
  allowedTools: string[];
  status?: string;
  isSelected?: boolean;
  onSelect?: () => void;
}

export const AgentNode: React.FC<AgentNodeProps> = ({
  id,
  name,
  role,
  model,
  allowedPeers,
  allowedTools,
  status = 'idle',
  isSelected = false,
  onSelect,
}) => {
  return (
    <div
      onClick={onSelect}
      className="glass-panel"
      style={{
        padding: '16px',
        width: '260px',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        borderColor: isSelected ? 'var(--accent-primary)' : 'var(--border-color)',
        boxShadow: isSelected ? '0 0 20px rgba(99, 102, 241, 0.35)' : 'none',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              padding: '6px',
              borderRadius: '8px',
              background: 'rgba(99, 102, 241, 0.2)',
              color: 'var(--accent-glow)',
            }}
          >
            <Bot size={18} />
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '14px', color: '#f8fafc' }}>{name}</div>
            <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'capitalize' }}>{role}</div>
          </div>
        </div>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <TrsmNodeGuardBadge nodeId={id} status={status} isEnforced={true} />
      </div>

      <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Users size={14} color="#64748b" />
          <span>Peers: {allowedPeers.length > 0 ? allowedPeers.join(', ') : 'None'}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Wrench size={14} color="#64748b" />
          <span>Tools: {allowedTools.length > 0 ? allowedTools.join(', ') : 'None'}</span>
        </div>
      </div>
    </div>
  );
};
