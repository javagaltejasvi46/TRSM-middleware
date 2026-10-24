import React, { useState } from 'react';
import { WorkflowCanvas } from '../components/WorkflowCanvas/WorkflowCanvas';
import { RunControls } from '../components/RunControls/RunControls';
import { TraceExplorer } from '../components/TraceExplorer/TraceExplorer';
import { MetricsPanel } from '../components/MetricsPanel/MetricsPanel';
import { ReviewModal } from '../components/ReviewModal/ReviewModal';
import { runsApi, RunSummary } from '../api/runs';
import { eventsApi } from '../api/events';
import { metricsApi } from '../api/metrics';
import { reviewsApi, ReviewRecord } from '../api/reviews';
import { AuditEvent, RunMetrics, WorkflowConfig } from '../types';

export const PlaygroundPage: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [runStatus, setRunStatus] = useState<string>('idle');
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [metrics, setMetrics] = useState<RunMetrics | null>(null);
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowConfig | null>(null);
  const [nodeStatusMap, setNodeStatusMap] = useState<Record<string, string>>({});

  // Human-in-the-Loop review state
  const [pendingReview, setPendingReview] = useState<ReviewRecord | null>(null);
  const [isReviewOpen, setIsReviewOpen] = useState(false);

  const handleStartRun = async (task: string, enableTrsm: boolean, useOllama: boolean) => {
    setIsRunning(true);
    setRunStatus('running');

    // Set initial node states to running/idle
    const initStatuses: Record<string, string> = {};
    if (currentWorkflow) {
      currentWorkflow.nodes.forEach((n, i) => {
        initStatuses[n.node_id] = i === 0 ? 'running' : 'idle';
      });
    }
    setNodeStatusMap(initStatuses);

    try {
      const runResult: RunSummary = await runsApi.start({
        workflow: currentWorkflow || undefined,
        task,
        enable_trsm: enableTrsm,
        use_ollama: useOllama,
      });

      setActiveRunId(runResult.run_id);
      setRunStatus(runResult.status);

      // Fetch trace events
      const runEvents = await eventsApi.getEvents(runResult.run_id);
      setEvents(runEvents);

      // Fetch metrics
      const runMetrics = await metricsApi.getRunMetrics(runResult.run_id);
      setMetrics(runMetrics);

      // Update node statuses on canvas based on execution events
      const finalStatuses: Record<string, string> = {};
      runEvents.forEach((evt) => {
        if (evt.policy_decision === 'BLOCK') {
          finalStatuses[evt.actor_id] = 'blocked';
        } else if (evt.policy_decision === 'QUARANTINE') {
          finalStatuses[evt.actor_id] = 'quarantined';
        } else if (evt.policy_decision === 'REVIEW') {
          finalStatuses[evt.actor_id] = 'review_required';
        } else if (!finalStatuses[evt.actor_id]) {
          finalStatuses[evt.actor_id] = 'completed';
        }
      });
      setNodeStatusMap(finalStatuses);

      // Check if any reviews are pending for this run
      const reviews = await reviewsApi.list();
      const runReview = reviews.find((r) => r.run_id === runResult.run_id && r.status === 'pending');
      if (runReview) {
        setPendingReview(runReview);
        setIsReviewOpen(true);
      }
    } catch (err: any) {
      console.error('Run execution error:', err);
      setRunStatus('failed');
    } finally {
      setIsRunning(false);
    }
  };

  const handleReviewResolved = (reviewId: string, decision: 'ALLOW' | 'BLOCK') => {
    setPendingReview(null);
    setIsReviewOpen(false);
    if (activeRunId) {
      // Refresh events
      eventsApi.getEvents(activeRunId).then(setEvents).catch(() => {});
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', minHeight: 'calc(100vh - 64px)', padding: '24px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            TRSM Studio Playground
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8' }}>
            Zero-Trust mediation for LangGraph multi-agent workflows with real-time threat interception
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span
            style={{
              fontSize: '11px',
              padding: '4px 10px',
              borderRadius: '6px',
              background: 'rgba(99, 102, 241, 0.15)',
              color: '#818cf8',
              border: '1px solid rgba(99, 102, 241, 0.35)',
              fontWeight: 600,
            }}
          >
            TRSM Engine: Active (v1.0.0)
          </span>
        </div>
      </div>

      {/* Main Studio Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '20px', flex: 1 }}>
        {/* Left Column: Interactive React Flow Canvas & Metrics Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <WorkflowCanvas
            onWorkflowChange={setCurrentWorkflow}
            runStatusMap={nodeStatusMap}
            activeRunId={activeRunId}
          />
          <MetricsPanel metrics={metrics} />
        </div>

        {/* Right Column: Execution Controls & Audit Trace Stream */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <RunControls
            isRunning={isRunning}
            onStartRun={handleStartRun}
            runStatus={runStatus}
          />
          <TraceExplorer events={events} />
        </div>
      </div>

      {/* Human-in-the-Loop Review Modal */}
      <ReviewModal
        review={pendingReview}
        isOpen={isReviewOpen}
        onClose={() => setIsReviewOpen(false)}
        onResolved={handleReviewResolved}
      />
    </div>
  );
};
