import React, { useCallback, useMemo, useState } from 'react';
import { MousePointerClick } from 'lucide-react';
import { WorkflowCanvas } from '../components/WorkflowCanvas/WorkflowCanvas';
import { NodeConfigPanel } from '../components/NodeConfigPanel/NodeConfigPanel';
import { WorkflowToolbar } from '../components/WorkflowToolbar/WorkflowToolbar';
import { RunControls } from '../components/RunControls/RunControls';
import { TraceExplorer } from '../components/TraceExplorer/TraceExplorer';
import { MetricsPanel } from '../components/MetricsPanel/MetricsPanel';
import { RunStatusPanel, type RunPanelState } from '../components/RunStatusPanel/RunStatusPanel';
import { ApiError } from '../api/client';
import { runsApi } from '../api/runs';
import { eventsApi } from '../api/events';
import { metricsApi } from '../api/metrics';
import { AgentNodeConfig, AgentRole, AuditEvent, RunMetrics, RunSummary, WorkflowConfig } from '../types';
import {
  addNode,
  addPeer,
  createAgentNode,
  deleteNode,
  executionSignature,
  moveNode,
  removePeer,
  setEntryNode,
  toWorkflowConfig,
  updateNode,
  type XYPosition,
} from '../lib/workflowGraph';
import { PRELOADED_WORKFLOWS } from '../lib/preloadedWorkflows';
import { runPreChecks } from '../lib/workflowChecks';
import { deriveNodeStates, deriveRouteDecisions, runTiming } from '../lib/runState';

/** Everything known about the last run, as returned by the backend. */
interface RunRecord {
  summary: RunSummary;
  /** executionSignature() of the workflow that was sent, to detect later edits. */
  signature: string;
  nodeIds: string[];
  events: AuditEvent[] | null;
  eventsError: string | null;
  metrics: RunMetrics | null;
  metricsError: string | null;
}

/** Stable empty list so effects keyed on `events` don't fire on every render. */
const NO_EVENTS: AuditEvent[] = [];

const errorText = (e: unknown) => (e instanceof ApiError ? e.message : (e as Error)?.message ?? String(e));

export const PlaygroundPage: React.FC = () => {
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string>(PRELOADED_WORKFLOWS[0].id);
  const [workflow, setWorkflow] = useState<WorkflowConfig>(PRELOADED_WORKFLOWS[0].workflow);
  const [enableTrsm, setEnableTrsm] = useState<boolean>(true);
  const [task, setTask] = useState<string>(PRELOADED_WORKFLOWS[0].defaultTask);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [pending, setPending] = useState<{ enableTrsm: boolean; sentAt: string } | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [run, setRun] = useState<RunRecord | null>(null);
  const [focusAgent, setFocusAgent] = useState<{ id: string; nonce: number } | null>(null);

  const preChecks = useMemo(() => runPreChecks(workflow), [workflow]);
  const selectedNode = workflow.nodes.find((n) => n.node_id === selectedNodeId) ?? null;
  const signature = useMemo(() => executionSignature(workflow), [workflow]);
  const stale = run !== null && run.signature !== signature;
  const events = run?.events ?? NO_EVENTS;

  const nodeStates = useMemo(
    () => (run?.events ? deriveNodeStates(run.events, run.nodeIds, run.summary.status) : null),
    [run],
  );
  const routeDecisions = useMemo(() => (run?.events ? deriveRouteDecisions(run.events) : undefined), [run]);
  const nodeStatuses = useMemo(
    () => (nodeStates && !stale ? Object.fromEntries(Object.entries(nodeStates).map(([id, s]) => [id, s.status])) : undefined),
    [nodeStates, stale],
  );

  // Gateway counts come only from audit events the backend returned for the last run.
  const gatewayStats = useMemo(() => {
    if (!run?.events || stale) return { mediated: null, blocked: null };
    return {
      mediated: run.events.filter((e) => e.event_type === 'message.policy_decided').length,
      blocked: run.events.filter((e) => e.event_type === 'message.blocked' || e.event_type === 'message.quarantined').length,
    };
  }, [run, stale]);

  const panelState: RunPanelState = pending
    ? { kind: 'running', ...pending }
    : runError
      ? { kind: 'error', message: runError }
      : run
        ? {
            kind: 'done',
            summary: run.summary,
            timing: runTiming(run.events ?? []),
            nodeStates,
            eventsError: run.eventsError,
            metricsError: run.metricsError,
            stale,
          }
        : { kind: 'idle' };

  const handleSelectPreloadedWorkflow = useCallback((id: string) => {
    setSelectedWorkflowId(id);
    const preloaded = PRELOADED_WORKFLOWS.find((p) => p.id === id);
    if (preloaded) {
      setWorkflow(preloaded.workflow);
      setTask(preloaded.defaultTask);
      setSelectedNodeId(null);
    }
  }, []);

  const handleAddNode = useCallback(
    (role: AgentRole, position: XYPosition) => {
      const node = createAgentNode(role, workflow.nodes.map((n) => n.node_id), position);
      setSelectedWorkflowId('custom');
      setWorkflow((wf) => addNode(wf, node));
      setSelectedNodeId(node.node_id);
    },
    [workflow.nodes],
  );

  const handleDeleteNodes = useCallback((ids: string[]) => {
    setSelectedWorkflowId('custom');
    setWorkflow((wf) => ids.reduce(deleteNode, wf));
    setSelectedNodeId((cur) => (cur && ids.includes(cur) ? null : cur));
  }, []);

  const handleApply = useCallback(
    (next: AgentNodeConfig) => {
      if (!selectedNodeId) return;
      setSelectedWorkflowId('custom');
      setWorkflow((wf) => updateNode(wf, selectedNodeId, next));
      setSelectedNodeId(next.node_id);
    },
    [selectedNodeId],
  );

  const handleStartRun = async (task: string, enableTrsm: boolean) => {
    const sent = toWorkflowConfig(workflow);
    setPending({ enableTrsm, sentAt: new Date().toISOString() });
    setRunError(null);
    setRun(null);
    setFocusAgent(null);
    try {
      // Run the workflow drawn on the canvas, not the backend's built-in default.
      const summary = await runsApi.start({ task, enable_trsm: enableTrsm, workflow: sent });
      // Events and metrics are fetched independently: one failing must not hide the other
      // or make the run look like something it was not.
      const [ev, mt] = await Promise.allSettled([eventsApi.getEvents(summary.run_id), metricsApi.getRunMetrics(summary.run_id)]);
      setRun({
        summary,
        signature: executionSignature(sent),
        nodeIds: sent.nodes.map((n) => n.node_id),
        events: ev.status === 'fulfilled' ? ev.value : null,
        eventsError: ev.status === 'rejected' ? errorText(ev.reason) : null,
        metrics: mt.status === 'fulfilled' ? mt.value : null,
        metricsError: mt.status === 'rejected' ? errorText(mt.reason) : null,
      });
    } catch (err) {
      setRunError(errorText(err));
    } finally {
      setPending(null);
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
            selectedWorkflowId={selectedWorkflowId}
            onSelectPreloadedWorkflow={handleSelectPreloadedWorkflow}
            onRename={(name) => {
              setSelectedWorkflowId('custom');
              setWorkflow((wf) => ({ ...wf, name }));
            }}
            onImport={(wf) => {
              setWorkflow(wf);
              setSelectedWorkflowId('custom');
              setSelectedNodeId(null);
            }}
          />

          <div className="surface" style={{ height: '560px', overflow: 'hidden' }} aria-label="Workflow canvas">
            <WorkflowCanvas
              workflow={workflow}
              selectedNodeId={selectedNodeId}
              gatewayStats={gatewayStats}
              enableTrsm={enableTrsm}
              onToggleTrsm={() => setEnableTrsm((prev) => !prev)}
              nodeStatuses={nodeStatuses}
              routeDecisions={stale ? undefined : routeDecisions}
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

          <MetricsPanel metrics={run?.metrics ?? null} />
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
          <RunControls
            isRunning={pending !== null}
            enableTrsm={enableTrsm}
            task={task}
            onTaskChange={setTask}
            selectedWorkflowId={selectedWorkflowId}
            onSelectWorkflowId={handleSelectPreloadedWorkflow}
            onStartRun={(t, trsm) => handleStartRun(t, trsm)}
            blockedReason={preChecks.errors.length ? `Fix ${preChecks.errors.length} pre-check error${preChecks.errors.length > 1 ? 's' : ''} above before running.` : null}
          />
          <RunStatusPanel state={panelState} onViewAgentEvents={(id) => setFocusAgent({ id, nonce: Date.now() })} />
          <TraceExplorer events={events} focusAgent={focusAgent} />
        </div>
      </div>
    </div>
  );
};
