import React, { useCallback, useState, useEffect } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  BackgroundVariant,
} from '@xyflow/react';
import { Plus, Save, CheckCircle2, AlertCircle, RefreshCw, FolderOpen } from 'lucide-react';
import { AgentNode, AgentNodeData } from '../AgentNode/AgentNode';
import { GatewayNode, GatewayNodeData } from '../CommunicationGateway/GatewayNode';
import { NodeConfigPanel } from '../NodeConfigPanel/NodeConfigPanel';
import { workflowsApi } from '../../api/workflows';
import { WorkflowConfig, AgentNodeConfig, AgentRole, WorkflowEdge } from '../../types';

const nodeTypes = {
  agentNode: AgentNode,
  gatewayNode: GatewayNode,
};

// Initial default 3-agent software engineering workflow layout
const INITIAL_AGENT_CONFIGS: AgentNodeConfig[] = [
  {
    node_id: 'backend_agent',
    name: 'Backend Agent',
    role: 'backend',
    model: 'llama3:8b',
    instructions: 'Handle customer API requests and coordinate with database manager.',
    allowed_peers: ['db_manager_agent'],
    allowed_tools: ['customer_db'],
    timeout_seconds: 30,
    call_limit: 10,
  },
  {
    node_id: 'db_manager_agent',
    name: 'DB Manager Agent',
    role: 'db_manager',
    model: 'llama3:8b',
    instructions: 'Manage profile queries, validations, and workflow memory storage.',
    allowed_peers: ['qa_agent'],
    allowed_tools: ['customer_db', 'workflow_memory'],
    timeout_seconds: 30,
    call_limit: 10,
  },
  {
    node_id: 'qa_agent',
    name: 'QA Agent',
    role: 'qa',
    model: 'llama3:8b',
    instructions: 'Execute regression test suites and verify integrity.',
    allowed_peers: [],
    allowed_tools: ['test_suite'],
    timeout_seconds: 30,
    call_limit: 10,
  },
];

interface WorkflowCanvasProps {
  onWorkflowChange?: (workflow: WorkflowConfig) => void;
  runStatusMap?: Record<string, string>;
  activeRunId?: string | null;
}

export const WorkflowCanvas: React.FC<WorkflowCanvasProps> = ({
  onWorkflowChange,
  runStatusMap = {},
  activeRunId = null,
}) => {
  const [agentConfigs, setAgentConfigs] = useState<AgentNodeConfig[]>(INITIAL_AGENT_CONFIGS);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [validationMsg, setValidationMsg] = useState<{ is_valid: boolean; text: string } | null>(null);
  const [savedWorkflows, setSavedWorkflows] = useState<WorkflowConfig[]>([]);

  // Convert agentConfigs to React Flow nodes with Gateway in the center
  const buildInitialNodes = (): Node[] => {
    return [
      {
        id: 'backend_agent',
        type: 'agentNode',
        position: { x: 50, y: 150 },
        data: {
          ...INITIAL_AGENT_CONFIGS[0],
          status: runStatusMap['backend_agent'] || 'idle',
        },
      },
      {
        id: 'trsm_gateway',
        type: 'gatewayNode',
        position: { x: 380, y: 140 },
        data: {
          totalMediated: 0,
          totalBlocked: 0,
          policyVersion: '1.0.0',
        },
      },
      {
        id: 'db_manager_agent',
        type: 'agentNode',
        position: { x: 730, y: 150 },
        data: {
          ...INITIAL_AGENT_CONFIGS[1],
          status: runStatusMap['db_manager_agent'] || 'idle',
        },
      },
      {
        id: 'qa_agent',
        type: 'agentNode',
        position: { x: 1060, y: 150 },
        data: {
          ...INITIAL_AGENT_CONFIGS[2],
          status: runStatusMap['qa_agent'] || 'idle',
        },
      },
    ];
  };

  const initialEdges: Edge[] = [
    {
      id: 'e_backend_gw',
      source: 'backend_agent',
      target: 'trsm_gateway',
      targetHandle: 'in-left',
      animated: true,
      style: { stroke: '#818cf8', strokeWidth: 2 },
    },
    {
      id: 'e_gw_db',
      source: 'trsm_gateway',
      target: 'db_manager_agent',
      sourceHandle: 'out-right',
      animated: true,
      style: { stroke: '#818cf8', strokeWidth: 2 },
    },
    {
      id: 'e_db_qa',
      source: 'db_manager_agent',
      target: 'qa_agent',
      animated: false,
      style: { stroke: '#64748b', strokeWidth: 1.5, strokeDasharray: '4 4' },
    },
  ];

  const [nodes, setNodes, onNodesChange] = useNodesState(buildInitialNodes());
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync node runtime statuses from parent run updates
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.type === 'agentNode') {
          const st = runStatusMap[node.id] || 'idle';
          return {
            ...node,
            data: {
              ...(node.data as any),
              status: st,
            },
          };
        }
        return node;
      })
    );
  }, [runStatusMap, setNodes]);

  // Load existing saved workflows on mount
  useEffect(() => {
    workflowsApi.list().then(setSavedWorkflows).catch(() => {});
  }, []);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#818cf8' } }, eds)),
    [setEdges]
  );

  const handleNodeClick = (_: React.MouseEvent, node: Node) => {
    if (node.type === 'agentNode') {
      setSelectedNodeId(node.id);
    }
  };

  // Add agent node
  const handleAddAgent = (role: AgentRole) => {
    const newId = `${role}_agent_${Date.now().toString().slice(-4)}`;
    const newConfig: AgentNodeConfig = {
      node_id: newId,
      name: `${role.toUpperCase()} Agent`,
      role,
      model: 'llama3:8b',
      instructions: `Perform tasks specialized as ${role}.`,
      allowed_peers: [],
      allowed_tools: role === 'qa' ? ['test_suite'] : role === 'db_manager' ? ['customer_db'] : ['customer_db'],
      timeout_seconds: 30,
      call_limit: 10,
    };

    setAgentConfigs((prev) => [...prev, newConfig]);
    const newNode: Node = {
      id: newId,
      type: 'agentNode',
      position: { x: 100 + (nodes.length * 60) % 600, y: 350 },
      data: {
        ...newConfig,
        status: 'idle',
      },
    };
    setNodes((nds) => [...nds, newNode]);
    setSelectedNodeId(newId);
  };

  // Update node configuration from drawer
  const handleUpdateNode = (updatedConfig: AgentNodeConfig) => {
    setAgentConfigs((prev) =>
      prev.map((c) => (c.node_id === updatedConfig.node_id ? updatedConfig : c))
    );
    setNodes((nds) =>
      nds.map((node) =>
        node.id === updatedConfig.node_id
          ? {
              ...node,
              data: {
                ...(node.data as any),
                ...updatedConfig,
              },
            }
          : node
      )
    );
  };

  // Delete node
  const handleDeleteNode = (nodeId: string) => {
    setAgentConfigs((prev) => prev.filter((c) => c.node_id !== nodeId));
    setNodes((nds) => nds.filter((n) => n.id !== nodeId));
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
    setSelectedNodeId(null);
  };

  // Build current workflow configuration object
  const getCurrentWorkflowConfig = (): WorkflowConfig => {
    const rawEdges: WorkflowEdge[] = edges
      .filter((e) => e.source !== 'trsm_gateway' && e.target !== 'trsm_gateway')
      .map((e) => ({
        source_node_id: e.source,
        target_node_id: e.target,
      }));

    // If edges connect via gateway, bridge source to target
    edges.forEach((e) => {
      if (e.target === 'trsm_gateway') {
        const downstream = edges.find((d) => d.source === 'trsm_gateway');
        if (downstream) {
          rawEdges.push({
            source_node_id: e.source,
            target_node_id: downstream.target,
          });
        }
      }
    });

    return {
      workflow_id: 'active_canvas_workflow',
      name: 'TRSM Orchestrated Workflow',
      version: '1.0.0',
      description: 'Configured on visual playground canvas',
      entry_node_id: agentConfigs[0]?.node_id || 'backend_agent',
      nodes: agentConfigs,
      edges: rawEdges,
    };
  };

  // Notify parent of workflow updates
  useEffect(() => {
    if (onWorkflowChange) {
      onWorkflowChange(getCurrentWorkflowConfig());
    }
  }, [agentConfigs, edges]);

  // Validate workflow topology
  const handleValidate = async () => {
    const wf = getCurrentWorkflowConfig();
    try {
      const res = await workflowsApi.validate(wf);
      if (res.is_valid) {
        setValidationMsg({ is_valid: true, text: 'Topology Valid: All nodes, entry points, and edge channels adhere to policy.' });
      } else {
        setValidationMsg({ is_valid: false, text: `Validation Failed: ${res.errors.join('; ')}` });
      }
    } catch (err: any) {
      setValidationMsg({ is_valid: false, text: `Server error: ${err.message}` });
    }
    setTimeout(() => setValidationMsg(null), 5000);
  };

  // Save workflow to backend
  const handleSave = async () => {
    const wf = getCurrentWorkflowConfig();
    try {
      await workflowsApi.create(wf);
      setValidationMsg({ is_valid: true, text: `Workflow saved successfully to SQLite database!` });
      const updated = await workflowsApi.list();
      setSavedWorkflows(updated);
    } catch (err: any) {
      setValidationMsg({ is_valid: false, text: `Failed to save: ${err.message}` });
    }
    setTimeout(() => setValidationMsg(null), 5000);
  };

  // Reset to default
  const handleReset = () => {
    setAgentConfigs(INITIAL_AGENT_CONFIGS);
    setNodes(buildInitialNodes());
    setEdges(initialEdges);
    setSelectedNodeId(null);
  };

  const selectedNode = agentConfigs.find((c) => c.node_id === selectedNodeId) || null;

  return (
    <div
      className="glass-panel"
      style={{
        height: '560px',
        width: '100%',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        border: '1px solid var(--border-color)',
        borderRadius: '16px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
      }}
    >
      {/* Canvas Top Toolbar */}
      <div
        style={{
          padding: '12px 18px',
          background: 'rgba(15, 23, 42, 0.95)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '13px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em' }}>
            Multi-Agent Studio
          </span>
          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8' }}>
            LangGraph DAG
          </span>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Add Agent Dropdown */}
          <div style={{ display: 'flex', gap: '4px' }}>
            {(['backend', 'db_manager', 'qa', 'devops'] as AgentRole[]).map((r) => (
              <button
                key={r}
                onClick={() => handleAddAgent(r)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '5px 9px',
                  borderRadius: '6px',
                  background: 'rgba(30, 41, 59, 0.8)',
                  border: '1px solid #475569',
                  color: '#cbd5e1',
                  fontSize: '11px',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                <Plus size={12} color="var(--accent-glow)" />
                <span style={{ textTransform: 'capitalize' }}>{r.replace('_', ' ')}</span>
              </button>
            ))}
          </div>

          <div style={{ width: '1px', height: '20px', background: '#334155', margin: '0 4px' }} />

          {/* Validate Button */}
          <button
            onClick={handleValidate}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '6px 12px',
              borderRadius: '6px',
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.4)',
              color: '#10b981',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <CheckCircle2 size={13} />
            <span>Validate</span>
          </button>

          {/* Save Button */}
          <button
            onClick={handleSave}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '6px 12px',
              borderRadius: '6px',
              background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
              border: 'none',
              color: '#ffffff',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 0 12px rgba(99, 102, 241, 0.35)',
            }}
          >
            <Save size={13} />
            <span>Save</span>
          </button>

          {/* Reset Button */}
          <button
            onClick={handleReset}
            title="Reset to default SE 3-agent layout"
            style={{
              padding: '6px 8px',
              borderRadius: '6px',
              background: 'rgba(30, 41, 59, 0.8)',
              border: '1px solid #475569',
              color: '#94a3b8',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      {/* Validation Banner */}
      {validationMsg && (
        <div
          style={{
            position: 'absolute',
            top: '55px',
            left: '20px',
            right: '20px',
            padding: '10px 14px',
            borderRadius: '8px',
            background: validationMsg.is_valid ? 'rgba(16, 185, 129, 0.95)' : 'rgba(244, 63, 94, 0.95)',
            color: '#ffffff',
            fontSize: '12px',
            fontWeight: 600,
            zIndex: 20,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 15px rgba(0,0,0,0.4)',
          }}
        >
          {validationMsg.is_valid ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{validationMsg.text}</span>
        </div>
      )}

      {/* Main Interactive React Flow Area */}
      <div style={{ flex: 1, width: '100%', height: '100%', background: '#070a12' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={handleNodeClick}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
        >
          <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#334155" />
          <Controls />
          <MiniMap
            nodeColor={(n) => (n.type === 'gatewayNode' ? '#818cf8' : '#38bdf8')}
            maskColor="rgba(7, 10, 18, 0.7)"
          />
        </ReactFlow>
      </div>

      {/* Slide-out Node Configuration Panel */}
      <NodeConfigPanel
        node={selectedNode}
        allNodes={agentConfigs}
        isOpen={Boolean(selectedNodeId)}
        onClose={() => setSelectedNodeId(null)}
        onUpdate={handleUpdateNode}
        onDelete={handleDeleteNode}
      />
    </div>
  );
};
