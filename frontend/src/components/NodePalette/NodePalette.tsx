import React from 'react';
import { Plus } from 'lucide-react';
import { AgentRole } from '../../types';
import { AGENT_ROLES, ROLE_LABELS } from '../../lib/workflowGraph';

export const ROLE_DRAG_TYPE = 'application/x-trsm-agent-role';

interface NodePaletteProps {
  onAdd: (role: AgentRole) => void;
}

/** Drag a role onto the canvas, or click it to add one in a free spot (single-pointer alternative). */
export const NodePalette: React.FC<NodePaletteProps> = ({ onAdd }) => (
  <div
    role="group"
    aria-labelledby="palette-title"
    style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '8px', padding: '10px 12px', borderBottom: '1px solid var(--border-color)' }}
  >
    <span id="palette-title" style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginRight: '4px' }}>
      Add agent
    </span>
    {AGENT_ROLES.map((role) => (
      <button
        key={role}
        type="button"
        draggable
        onDragStart={(e) => {
          e.dataTransfer.setData(ROLE_DRAG_TYPE, role);
          e.dataTransfer.effectAllowed = 'move';
        }}
        onClick={() => onAdd(role)}
        aria-label={`Add ${ROLE_LABELS[role]} agent`}
        className="btn btn-secondary"
        style={{ cursor: 'grab' }}
      >
        <Plus size={14} aria-hidden="true" />
        {ROLE_LABELS[role]}
      </button>
    ))}
    <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginLeft: 'auto' }}>Drag onto the canvas or click to add</span>
  </div>
);
