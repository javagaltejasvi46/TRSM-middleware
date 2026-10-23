import React, { useState } from 'react';
import { AgentNode } from '../components/AgentNode/AgentNode';
import { GatewayNode } from '../components/CommunicationGateway/GatewayNode';
import { RunControls } from '../components/RunControls/RunControls';
import { TraceExplorer } from '../components/TraceExplorer/TraceExplorer';
import { MetricsPanel } from '../components/MetricsPanel/MetricsPanel';
import { runsApi } from '../api/runs';
import { eventsApi } from '../api/events';
import { metricsApi } from '../api/metrics';
import { AuditEvent, RunMetrics } from '../types';

export const PlaygroundPage: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [metrics, setMetrics] = useState<RunMetrics | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>('backend_agent');

  const handleStartRun = async (task: string, enableTrsm: boolean) => {
    setIsRunning(true);
    try {
      const runResult = await runsApi.start({ task, enable_trsm: enableTrsm });
      setActiveRunId(runResult.run_id);

      // Fetch trace events
      const runEvents = await eventsApi.getEvents(runResult.run_id);
      setEvents(runEvents);

      // Fetch metrics
      const runMetrics = await metricsApi.getRunMetrics(runResult.run_id);
      setMetrics(runMetrics);
    } catch (err) {
      console.error('Run execution error:', err);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', minHeight: '100vh', padding: '24px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            TRSM Playground & Workflow Orchestrator
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8' }}>
            Trust, Risk, and Security Management middleware for agentic multi-agent systems
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '12px', padding: '4px 10px', borderRadius: '6px', background: 'rgba(99, 102, 241, 0.1)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
            Protocol: Zero-Trust Inter-Agent Mediation
          </span>
        </div>
      </div>

      {/* Main Layout Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px', flex: 1 }}>
        {/* Left Column: Canvas and Metrics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Workflow Canvas */}
          <div
            className="glass-panel"
            style={{
              padding: '24px',
              minHeight: '440px',
              position: 'relative',
              background: 'radial-gradient(circle at 50% 50%, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.8) 100%)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#cbd5e1' }}>Visual Workflow Canvas (LangGraph Topology)</span>
              <span style={{ fontSize: '11px', color: '#64748b' }}>Every node equipped with TRSM Node Guard</span>
            </div>

            {/* Simulated Nodes & Central Gateway Layout */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-around', margin: '40px 0' }}>
              <AgentNode
                id="backend_agent"
                name="Backend Agent"
                role="backend"
                model="llama3:8b"
                allowedPeers={['db_manager_agent']}
                allowedTools={['customer_db']}
                isSelected={selectedAgent === 'backend_agent'}
                onSelect={() => setSelectedAgent('backend_agent')}
              />

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                <GatewayNode />
              </div>

              <AgentNode
                id="db_manager_agent"
                name="DB Manager"
                role="db_manager"
                model="llama3:8b"
                allowedPeers={['qa_agent']}
                allowedTools={['customer_db', 'workflow_memory']}
                isSelected={selectedAgent === 'db_manager_agent'}
                onSelect={() => setSelectedAgent('db_manager_agent')}
              />

              <AgentNode
                id="qa_agent"
                name="QA Agent"
                role="qa"
                model="llama3:8b"
                allowedPeers={[]}
                allowedTools={['test_suite']}
                isSelected={selectedAgent === 'qa_agent'}
                onSelect={() => setSelectedAgent('qa_agent')}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#64748b' }}>
              <span>Arrows denote configured communication routes</span>
              <span>Central gateway strictly authorizes message envelopes before delivery</span>
            </div>
          </div>

          {/* Metrics Panel */}
          <MetricsPanel metrics={metrics} />
        </div>

        {/* Right Column: Execution Controls & Audit Trace */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <RunControls isRunning={isRunning} onStartRun={handleStartRun} />
          <TraceExplorer events={events} />
        </div>
      </div>
    </div>
  );
};
