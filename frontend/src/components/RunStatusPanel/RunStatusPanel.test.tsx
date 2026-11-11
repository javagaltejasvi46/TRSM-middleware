import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RunStatusPanel, type RunPanelState } from './RunStatusPanel';
import type { NodeRunState } from '../../lib/runState';

const ns = (over: Partial<NodeRunState>): NodeRunState => ({ status: 'completed', eventCount: 3, firstAt: null, lastAt: null, spanMs: 2, reasons: [], ...over });

const done = (over: Partial<Extract<RunPanelState, { kind: 'done' }>> = {}): RunPanelState => ({
  kind: 'done',
  summary: { run_id: 'run-123', workflow_id: 'wf', status: 'completed', enable_trsm: true, task: 't', total_messages: 1, total_tool_calls: 1, blocked_actions: 1 },
  timing: { startedAt: '2026-11-11T10:00:00.000Z', endedAt: '2026-11-11T10:00:00.012Z', durationMs: 12 },
  nodeStates: {
    backend_agent: ns({ status: 'blocked', reasons: ['THREAT_PROMPT_INJECTION'] }),
    qa_agent: ns({ status: 'not_reached', eventCount: 0, spanMs: null }),
  },
  eventsError: null,
  metricsError: null,
  stale: false,
  ...over,
});

describe('RunStatusPanel', () => {
  it('shows a failed request as an error and no run result', () => {
    render(<RunStatusPanel state={{ kind: 'error', message: '/api/runs returned HTTP 422: workflow.nodes: too short' }} onViewAgentEvents={vi.fn()} />);
    expect(screen.getByRole('alert')).toHaveTextContent('HTTP 422');
    expect(screen.queryByText(/Backend status/)).not.toBeInTheDocument();
  });

  it('shows the in-flight state while the backend runs', () => {
    render(<RunStatusPanel state={{ kind: 'running', enableTrsm: false, sentAt: '' }} onViewAgentEvents={vi.fn()} />);
    expect(screen.getByRole('status')).toHaveTextContent('baseline, no TRSM');
  });

  it('shows backend status, totals and per-agent derived states with reasons', () => {
    render(<RunStatusPanel state={done()} onViewAgentEvents={vi.fn()} />);
    expect(screen.getByText('Backend status: completed')).toBeVisible();
    expect(screen.getByText('run run-123')).toBeVisible();
    expect(screen.getByText(/Derived from audit events/)).toBeVisible();
    expect(screen.getByRole('status', { name: 'TRSM Node Guard for backend_agent: Blocked' })).toBeInTheDocument();
    expect(screen.getByRole('status', { name: 'TRSM Node Guard for qa_agent: Not reached' })).toBeInTheDocument();
    expect(screen.getByText('THREAT_PROMPT_INJECTION')).toBeVisible();
  });

  it('links an agent to its trace events, but not agents with no events', async () => {
    const onView = vi.fn();
    render(<RunStatusPanel state={done()} onViewAgentEvents={onView} />);
    await userEvent.setup().click(screen.getByRole('button', { name: 'View trace events for backend_agent' }));
    expect(onView).toHaveBeenCalledWith('backend_agent');
    expect(screen.queryByRole('button', { name: 'View trace events for qa_agent' })).not.toBeInTheDocument();
  });

  it('warns when results are stale or partially unavailable', () => {
    render(<RunStatusPanel state={done({ stale: true, nodeStates: null, eventsError: 'HTTP 500', metricsError: 'HTTP 404: Metrics not found' })} onViewAgentEvents={vi.fn()} />);
    expect(screen.getByText(/canvas changed after this run/)).toBeVisible();
    expect(screen.getByRole('alert')).toHaveTextContent('Audit events could not be loaded');
    expect(screen.getByText(/Metrics are unavailable/)).toBeVisible();
    expect(screen.queryByText('Agents in this run')).not.toBeInTheDocument();
  });
});
