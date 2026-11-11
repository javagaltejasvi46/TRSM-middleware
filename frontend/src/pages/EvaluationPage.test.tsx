import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuditEvent, RunMetrics, RunSummary } from '../types';

vi.mock('../api/runs', () => ({ runsApi: { start: vi.fn() } }));
vi.mock('../api/events', () => ({ eventsApi: { getEvents: vi.fn() } }));
vi.mock('../api/metrics', () => ({ metricsApi: { compareRuns: vi.fn() } }));

import { runsApi } from '../api/runs';
import { eventsApi } from '../api/events';
import { metricsApi } from '../api/metrics';
import { ApiError } from '../api/client';
import { EvaluationPage } from './EvaluationPage';

const start = vi.mocked(runsApi.start);
const getEvents = vi.mocked(eventsApi.getEvents);
const compare = vi.mocked(metricsApi.compareRuns);

const metric = (num: number, den: number) => ({ name: 'm', version: '1', value: den ? num / den : 1, available: true, numerator: num, denominator: den, metadata: {} });
const runMetrics = (id: string): RunMetrics => ({ run_id: id, css: metric(1, 1), tue: metric(0, 0), task_success: true, security_blocked_attacks: 2, total_messages: 1, total_tool_calls: 0, avg_latency_ms: 12.5, p95_latency_ms: 25 });

/** Fake backend: baseline never decides; protected BLOCKs adversarial tasks, ALLOWs benign ones. */
function fakeBackend() {
  let i = 0;
  const byRun: Record<string, AuditEvent[]> = {};
  start.mockImplementation(async ({ task, enable_trsm }) => {
    const run_id = `run-${++i}`;
    const adversarial = !/Retrieve customer profile|Check status of integration/.test(task);
    const decision = !enable_trsm ? null : adversarial ? 'BLOCK' : 'ALLOW';
    const base = { run_id, trace_id: 't', actor_id: 'backend_agent', trust_labels: [] as never[] };
    byRun[run_id] = [
      { ...base, event_id: `${run_id}-a`, timestamp: '2026-11-11T10:00:00.000Z', event_type: 'workflow.started', actor_id: 'orchestrator' },
      ...(decision ? [{ ...base, event_id: `${run_id}-b`, timestamp: '2026-11-11T10:00:00.002Z', event_type: 'message.policy_decided', policy_decision: decision, reason_code: decision === 'BLOCK' ? 'THREAT_PROMPT_INJECTION' : 'AUTHORIZED_PEER_COMMUNICATION' } as AuditEvent] : []),
      { ...base, event_id: `${run_id}-c`, timestamp: '2026-11-11T10:00:00.004Z', event_type: 'workflow.completed', actor_id: 'orchestrator' },
    ];
    const s: RunSummary = { run_id, workflow_id: 'default_se_workflow', status: 'completed', enable_trsm, task, total_messages: 1, total_tool_calls: 0, blocked_actions: decision === 'BLOCK' ? 1 : 0 };
    return s;
  });
  getEvents.mockImplementation(async (id: string) => byRun[id]);
  compare.mockImplementation(async (b: string, p: string) => ({ baseline_run_id: b, protected_run_id: p, baseline_metrics: runMetrics(b), protected_metrics: runMetrics(p), overhead_ms: 0, security_delta: '' }));
}

describe('EvaluationPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('lists the repository scenarios and shows no numbers before anything runs', () => {
    render(<EvaluationPage />);
    expect(screen.getByText('pi_direct_override_001')).toBeInTheDocument();
    expect(screen.getByText(/No results yet/)).toBeVisible();
    // The old hard-coded figures must be gone.
    expect(screen.queryByText('+12.5ms')).not.toBeInTheDocument();
    expect(screen.queryByText('0.0%')).not.toBeInTheDocument();
    expect(start).not.toHaveBeenCalled();
  });

  it('runs every scenario baseline then protected, and summarises only observed results', async () => {
    fakeBackend();
    const user = userEvent.setup();
    render(<EvaluationPage />);
    await user.click(screen.getByRole('button', { name: /Run all \d+ scenarios/ }));
    await waitFor(() => expect(screen.getByText(/8 of 8 scenarios have results/)).toBeInTheDocument(), { timeout: 5000 });

    expect(start).toHaveBeenCalledTimes(16);
    expect(start.mock.calls[0][0]).toMatchObject({ enable_trsm: false });
    expect(start.mock.calls[1][0]).toMatchObject({ enable_trsm: true });
    expect(start.mock.calls[0][0]).not.toHaveProperty('workflow');

    const summary = screen.getByRole('region', { name: /Summary of 8 completed trials/ });
    expect(within(summary).getByText('8/8')).toBeVisible(); // matched expected
    expect(within(summary).getByText('6/6')).toBeVisible(); // adversarial stopped with TRSM
    expect(within(summary).getByText('0/6')).toBeVisible(); // adversarial stopped without TRSM
    expect(within(summary).getByText('0/2')).toBeVisible(); // benign flagged
    expect(screen.getAllByText('Matches')).toHaveLength(8);
  });

  it('shows comparison details with placeholder fields labelled, not presented as data', async () => {
    fakeBackend();
    const user = userEvent.setup();
    render(<EvaluationPage />);
    await user.click(screen.getByRole('button', { name: 'Run pi_direct_override_001' }));
    await user.click(await screen.findByRole('button', { name: /Details/ }));
    // TUE is 0/0 in both runs: shown as n/a with the reason, not as the backend's 100%.
    expect(screen.getAllByText(/^n\/a \(nothing was proposed \(0\/0\)/)).toHaveLength(2);
    expect(screen.getByText(/counts twice/)).toBeInTheDocument();
    expect(screen.queryByText('12.5')).not.toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Not available from the API' })).toHaveTextContent('computed offline by scripts/run_evaluation.py');
  });

  it('records a failed trial as an error with no result', async () => {
    start.mockRejectedValue(new ApiError(500, '/api/runs', 'boom'));
    const user = userEvent.setup();
    render(<EvaluationPage />);
    await user.click(screen.getByRole('button', { name: 'Run pi_direct_override_001' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Trial failed, no result recorded: /api/runs returned HTTP 500: boom');
    expect(screen.getByText(/No results yet/)).toBeVisible();
  });
});
