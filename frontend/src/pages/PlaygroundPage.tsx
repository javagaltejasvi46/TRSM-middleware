import React, { useCallback, useMemo, useState } from 'react';
import { MousePointerClick } from 'lucide-react';
import { WorkflowCanvas } from '../components/WorkflowCanvas/WorkflowCanvas';
import { NodeConfigPanel } from '../components/NodeConfigPanel/NodeConfigPanel';
import { WorkflowToolbar } from '../components/WorkflowToolbar/WorkflowToolbar';
import { RunControls } from '../components/RunControls/RunControls';
import { TraceExplorer } from '../components/TraceExplorer/TraceExplorer';
import { MetricsPanel } from '../components/MetricsPanel/MetricsPanel';
import { runsApi } from '../api/runs';
import { eventsApi } from '../api/events';
import { metricsApi } from '../api/metrics';
import { AgentNodeConfig, AgentRole, AuditEvent, RunMetrics, WorkflowConfig } from '../types';
import {
  addNode,
  addPeer,
  createAgentNode,
  defaultWorkflow,
  deleteNode,
  moveNode,
  removePeer,
  setEntryNode,
  toWorkflowConfig,
  updateNode,
  type XYPosition,
} from '../lib/workflowGraph';
import { runPreChecks } from '../lib/workflowChecks';

export const PlaygroundPage: React.FC = () => {
  const [workflow, setWorkflow] = useState<WorkflowConfig>(defaultWorkflow);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [metrics, setMetrics] = useState<RunMetrics | null>(null);

  const preChecks = useMemo(() => runPreChecks(workflow), [workflow]);
  const selectedNode = workflow.nodes.find((n) => n.node_id === selectedNodeId) ?? null;

  // Gateway counts come only from audit events the backend returned for the last run.
  const gatewayStats = useMemo(() => {
    if (!activeRunId) return { mediated: null, blocked: null };
    return {
      mediated: events.filter((e) => e.event_type === 'message.policy_decided').length,
      blocked: events.filter((e) => e.event_type === 'message.blocked' || e.event_type === 'message.quarantined').length,
    };
  }, [activeRunId, events]);

  const handleAddNode = useCallback(
    (role: AgentRole, position: XYPosition) => {
      const node = createAgentNode(role, workflow.nodes.map((n) => n.node_id), position);
      setWorkflow((wf) => addNode(wf, node));
      setSelectedNodeId(node.node_id);
    },
    [workflow.nodes],
  );

  const handleDeleteNodes = useCallback((ids: string[]) => {
    setWorkflow((wf) => ids.reduce(deleteNode, wf));
    setSelectedNodeId((cur) => (cur && ids.includes(cur) ? null : cur));
  }, []);

  const handleApply = useCallback(
    (next: AgentNodeConfig) => {
      if (!selectedNodeId) return;
      setWorkflow((wf) => updateNode(wf, selectedNodeId, next));
      setSelectedNodeId(next.node_id);
    },
    [selectedNodeId],
  );

  const handleStartRun = async (task: string, enableTrsm: boolean) => {
    setIsRunning(true);
    try {
      // Run the workflow drawn on the canvas, not the backend's built-in default.
      const runResult = await runsApi.start({ task, enable_trsm: enableTrsm, workflow: toWorkflowConfig(workflow) });
      setActiveRunId(runResult.run_id);
      setEvents(await eventsApi.getEvents(runResult.run_id));
      setMetrics(await metricsApi.getRunMetrics(runResult.run_id));
    } catch (err) {
      console.error('Run execution error:', err);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '24px' }}>
      <div>
        <h1 style={{ fontSize: '22px', fontWeight: 700, letterSpacing: '-0.02em' }}>TRSM Playground</h1>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Configure agents and their allowed routes. Every message and tool call is decided by the backend TRSM gateways at run time.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 360px', gap: '20px', alignItems: 'start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', minWidth: 0 }}>
          <WorkflowToolbar
            workflow={workflow}
            preChecks={preChecks}
            onRename={(name) => setWorkflow((wf) => ({ ...wf, name }))}
            onImport={(wf) => {
              setWorkflow(wf);
              setSelectedNodeId(null);
            }}
          />

          <div className="surface" style={{ height: '560px', overflow: 'hidden' }} aria-label="Workflow canvas">
            <WorkflowCanvas
              workflow={workflow}
              selectedNodeId={selectedNodeId}
              gatewayStats={gatewayStats}
              onSelectNode={setSelectedNodeId}
              onAddNode={handleAddNode}
              onMoveNode={(id, pos) => setWorkflow((wf) => moveNode(wf, id, pos))}
              onDeleteNodes={handleDeleteNodes}
              onAddPeer={(s, t) => setWorkflow((wf) => addPeer(wf, s, t))}
              onRemovePeer={(s, t) => setWorkflow((wf) => removePeer(wf, s, t))}
            />
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '-12px' }}>
            Drag from a node's right handle to another node to allow it as a peer. Select a route or node and press Delete to remove it. A route is a configured path, not proof a message will be allowed.
          </p>

          <MetricsPanel metrics={metrics} />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {selectedNode ? (
            <NodeConfigPanel
              key={`${selectedNode.node_id}:${JSON.stringify(selectedNode)}`}
              node={selectedNode}
              otherNodeIds={workflow.nodes.map((n) => n.node_id).filter((id) => id !== selectedNode.node_id)}
              isEntry={workflow.entry_node_id === selectedNode.node_id}
              onApply={handleApply}
              onDelete={() => handleDeleteNodes([selectedNode.node_id])}
              onSetEntry={() => setWorkflow((wf) => setEntryNode(wf, selectedNode.node_id))}
            />
          ) : (
            <div className="surface" style={{ padding: '16px', display: 'flex', gap: '10px', alignItems: 'center', color: 'var(--text-secondary)', fontSize: '13px' }}>
              <MousePointerClick size={18} aria-hidden="true" />
              Select an agent on the canvas to configure it.
            </div>
          )}
          <RunControls isRunning={isRunning} onStartRun={handleStartRun} />
          <TraceExplorer events={events} />
        </div>
      </div>
    </div>
  );
};
