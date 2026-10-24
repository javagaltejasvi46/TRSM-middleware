import React from 'react';
import { X, Trash2, Shield, Wrench, Users, Bot, Sliders } from 'lucide-react';
import { AgentNodeConfig, AgentRole } from '../../types';

interface NodeConfigPanelProps {
  node: AgentNodeConfig | null;
  allNodes: AgentNodeConfig[];
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (updatedNode: AgentNodeConfig) => void;
  onDelete: (nodeId: string) => void;
}

const AVAILABLE_ROLES: AgentRole[] = ['backend', 'db_manager', 'qa', 'devops', 'custom'];
const AVAILABLE_TOOLS = [
  { id: 'customer_db', label: 'Customer DB (Profile read/write)' },
  { id: 'workflow_memory', label: 'Workflow Memory (Key-value store)' },
  { id: 'test_suite', label: 'Automated Test Suite' },
  { id: 'deployment_manager', label: 'Deployment Controller' },
  { id: 'code_linter', label: 'Code Quality Linter' },
];

export const NodeConfigPanel: React.FC<NodeConfigPanelProps> = ({
  node,
  allNodes,
  isOpen,
  onClose,
  onUpdate,
  onDelete,
}) => {
  if (!isOpen || !node) return null;

  const otherNodes = allNodes.filter((n) => n.node_id !== node.node_id);

  const togglePeer = (peerId: string) => {
    const peers = node.allowed_peers || [];
    const newPeers = peers.includes(peerId)
      ? peers.filter((p) => p !== peerId)
      : [...peers, peerId];
    onUpdate({ ...node, allowed_peers: newPeers });
  };

  const toggleTool = (toolId: string) => {
    const tools = node.allowed_tools || [];
    const newTools = tools.includes(toolId)
      ? tools.filter((t) => t !== toolId)
      : [...tools, toolId];
    onUpdate({ ...node, allowed_tools: newTools });
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: '64px',
        right: '0',
        width: '380px',
        height: 'calc(100vh - 64px)',
        background: 'rgba(15, 23, 42, 0.95)',
        backdropFilter: 'blur(20px)',
        borderLeft: '1px solid var(--border-color)',
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-10px 0 30px rgba(0, 0, 0, 0.5)',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sliders size={18} color="var(--accent-glow)" />
          <h2 style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>
            Node Configuration
          </h2>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '6px',
          }}
        >
          <X size={18} />
        </button>
      </div>

      {/* Content Form */}
      <div style={{ padding: '20px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Node ID & Display Name */}
        <div>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', display: 'block', marginBottom: '6px' }}>
            Node ID
          </label>
          <input
            type="text"
            value={node.node_id}
            disabled
            style={{
              width: '100%',
              padding: '8px 12px',
              borderRadius: '6px',
              background: 'rgba(30, 41, 59, 0.5)',
              border: '1px solid #334155',
              color: '#64748b',
              fontSize: '12px',
              fontFamily: 'monospace',
            }}
          />
        </div>

        <div>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
            Display Name
          </label>
          <input
            type="text"
            value={node.name}
            onChange={(e) => onUpdate({ ...node, name: e.target.value })}
            style={{
              width: '100%',
              padding: '8px 12px',
              borderRadius: '6px',
              background: 'rgba(30, 41, 59, 0.8)',
              border: '1px solid #475569',
              color: '#f8fafc',
              fontSize: '13px',
            }}
          />
        </div>

        {/* Role & Model */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
              Agent Role
            </label>
            <select
              value={node.role}
              onChange={(e) => onUpdate({ ...node, role: e.target.value as AgentRole })}
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '6px',
                background: 'rgba(30, 41, 59, 0.8)',
                border: '1px solid #475569',
                color: '#f8fafc',
                fontSize: '12px',
              }}
            >
              {AVAILABLE_ROLES.map((r) => (
                <option key={r} value={r}>
                  {r.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
              Model
            </label>
            <input
              type="text"
              value={node.model}
              onChange={(e) => onUpdate({ ...node, model: e.target.value })}
              placeholder="e.g. llama3:8b"
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                background: 'rgba(30, 41, 59, 0.8)',
                border: '1px solid #475569',
                color: '#f8fafc',
                fontSize: '12px',
              }}
            />
          </div>
        </div>

        {/* Allowed Peer Agents (Policy Matrix) */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Users size={14} color="#818cf8" />
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1' }}>
              Authorized Peer Agents
            </span>
          </div>
          <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '10px', borderRadius: '8px', border: '1px solid #334155' }}>
            {otherNodes.length === 0 ? (
              <span style={{ fontSize: '11px', color: '#64748b' }}>No other agents configured in workflow.</span>
            ) : (
              otherNodes.map((n) => {
                const isChecked = (node.allowed_peers || []).includes(n.node_id);
                return (
                  <label
                    key={n.node_id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '12px',
                      color: isChecked ? '#f8fafc' : '#94a3b8',
                      cursor: 'pointer',
                      padding: '4px 0',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => togglePeer(n.node_id)}
                      style={{ accentColor: 'var(--accent-primary)' }}
                    />
                    <span>{n.name} ({n.role})</span>
                  </label>
                );
              })
            )}
          </div>
        </div>

        {/* Allowed Tools / Resources */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Wrench size={14} color="#38bdf8" />
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1' }}>
              Authorized Tools & Data
            </span>
          </div>
          <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '10px', borderRadius: '8px', border: '1px solid #334155', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {AVAILABLE_TOOLS.map((tool) => {
              const isChecked = (node.allowed_tools || []).includes(tool.id);
              return (
                <label
                  key={tool.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '12px',
                    color: isChecked ? '#f8fafc' : '#94a3b8',
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleTool(tool.id)}
                    style={{ accentColor: '#38bdf8' }}
                  />
                  <span>{tool.label}</span>
                </label>
              );
            })}
          </div>
        </div>

        {/* System Prompt / Instructions */}
        <div>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
            System Instructions / Prompt
          </label>
          <textarea
            value={node.instructions || ''}
            onChange={(e) => onUpdate({ ...node, instructions: e.target.value })}
            placeholder="Agent task instructions..."
            rows={4}
            style={{
              width: '100%',
              padding: '8px 12px',
              borderRadius: '6px',
              background: 'rgba(30, 41, 59, 0.8)',
              border: '1px solid #475569',
              color: '#f8fafc',
              fontSize: '12px',
              fontFamily: 'inherit',
              resize: 'vertical',
            }}
          />
        </div>
      </div>

      {/* Footer Actions */}
      <div
        style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(15, 23, 42, 0.9)',
        }}
      >
        <button
          onClick={() => onDelete(node.node_id)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px',
            borderRadius: '6px',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#f43f5e',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <Trash2 size={14} />
          <span>Delete Node</span>
        </button>

        <button
          onClick={onClose}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            background: 'var(--accent-primary)',
            border: 'none',
            color: '#ffffff',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Done
        </button>
      </div>
    </div>
  );
};
