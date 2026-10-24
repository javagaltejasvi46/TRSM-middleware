import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Bot, Wrench, Users, Database, ShieldAlert, Cpu } from 'lucide-react';
import { TrsmNodeGuardBadge } from '../TrsmNodeGuardBadge/TrsmNodeGuardBadge';
import { AgentRole } from '../../types';

export interface AgentNodeData {
  id: string;
  name: string;
  role: AgentRole;
  model: string;
  allowedPeers: string[];
  allowedTools: string[];
  status?: string;
  instructions?: string;
  isEnforced?: boolean;
  onSelect?: () => void;
}

export const AgentNode: React.FC<NodeProps> = ({ id, data, selected }) => {
  const nodeData = (data as unknown as AgentNodeData) || {};
  const {
    name = id,
    role = 'backend',
    model = 'llama3:8b',
    allowedPeers = [],
    allowedTools = [],
    status = 'idle',
    isEnforced = true,
  } = nodeData;

  const getRoleIcon = () => {
    switch (role) {
      case 'db_manager':
        return <Database size={16} />;
      case 'qa':
        return <Wrench size={16} />;
      case 'devops':
        return <Cpu size={16} />;
      default:
        return <Bot size={16} />;
    }
  };

  const getStatusBorder = () => {
    if (status === 'blocked') return '#f43f5e';
    if (status === 'quarantined') return '#f59e0b';
    if (status === 'running') return '#38bdf8';
    if (status === 'completed') return '#10b981';
    if (selected) return 'var(--accent-glow)';
    return 'var(--border-color)';
  };

  const getStatusShadow = () => {
    if (status === 'blocked') return '0 0 20px rgba(244, 63, 94, 0.4)';
    if (status === 'quarantined') return '0 0 20px rgba(245, 158, 11, 0.35)';
    if (status === 'running') return '0 0 25px rgba(56, 189, 248, 0.45)';
    if (status === 'completed') return '0 0 15px rgba(16, 185, 129, 0.3)';
    if (selected) return '0 0 20px rgba(99, 102, 241, 0.35)';
    return 'none';
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: '16px',
        width: '270px',
        cursor: 'pointer',
        transition: 'all 0.25s ease',
        borderColor: getStatusBorder(),
        boxShadow: getStatusShadow(),
        position: 'relative',
        background: 'rgba(15, 23, 42, 0.9)',
      }}
    >
      {/* Target Handle (Left) */}
      <Handle
        type="target"
        position={Position.Left}
        id="in"
        style={{ background: '#818cf8', width: '10px', height: '10px' }}
      />

      {/* Header: Role icon, name, role pill */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              padding: '6px',
              borderRadius: '8px',
              background: 'rgba(99, 102, 241, 0.2)',
              color: 'var(--accent-glow)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {getRoleIcon()}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '13px', color: '#f8fafc' }}>{name}</div>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'capitalize' }}>{role}</div>
          </div>
        </div>

        {/* Status Indicator */}
        <span
          style={{
            fontSize: '10px',
            textTransform: 'uppercase',
            fontWeight: 700,
            padding: '2px 6px',
            borderRadius: '4px',
            background:
              status === 'blocked'
                ? 'rgba(244, 63, 94, 0.2)'
                : status === 'completed'
                ? 'rgba(16, 185, 129, 0.2)'
                : status === 'running'
                ? 'rgba(56, 189, 248, 0.2)'
                : 'rgba(51, 65, 85, 0.5)',
            color:
              status === 'blocked'
                ? '#f43f5e'
                : status === 'completed'
                ? '#10b981'
                : status === 'running'
                ? '#38bdf8'
                : '#94a3b8',
          }}
        >
          {status}
        </span>
      </div>

      {/* TRSM Node Guard Badge */}
      <div style={{ marginBottom: '10px' }}>
        <TrsmNodeGuardBadge nodeId={id} status={status} isEnforced={isEnforced} />
      </div>

      {/* Metadata summary */}
      <div style={{ fontSize: '11px', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '5px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Users size={13} color="#64748b" />
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            Peers: {allowedPeers.length > 0 ? allowedPeers.join(', ') : 'None'}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Wrench size={13} color="#64748b" />
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            Tools: {allowedTools.length > 0 ? allowedTools.join(', ') : 'None'}
          </span>
        </div>
        <div style={{ fontSize: '10px', color: '#64748b', fontStyle: 'italic', marginTop: '2px' }}>
          Model: {model}
        </div>
      </div>

      {/* Source Handle (Right) */}
      <Handle
        type="source"
        position={Position.Right}
        id="out"
        style={{ background: '#38bdf8', width: '10px', height: '10px' }}
      />
    </div>
  );
};
