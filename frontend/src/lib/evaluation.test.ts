import { describe, expect, it } from 'vitest';
import { conditionResult, matchesExpected, median, ratio, summarizeTrials, type TrialResult } from './evaluation';
import { AuditEvent, PolicyDecisionEnum, RunSummary } from '../types';
import type { Scenario } from './scenarios';

let n = 0;
const ev = (over: Partial<AuditEvent>): AuditEvent => ({
  event_id: `e${++n}`,
  run_id: 'r',
  trace_id: 't',
  timestamp: new Date(Date.UTC(2026, 10, 11, 10, 0, 0, n)).toISOString(),
  actor_id: 'x',
  event_type: 'message.proposed',
  trust_labels: [],
  ...over,
});
const summary = (over: Partial<RunSummary> = {}): RunSummary => ({ run_id: 'r', workflow_id: 'w', status: 'completed', enable_trsm: true, task: 't', total_messages: 1, total_tool_calls: 1, blocked_actions: 0, ...over });
const scenario = (label: 'benign' | 'adversarial', expected: PolicyDecisionEnum): Scenario => ({ id: `${label}-${expected}`, name: 'n', category: 'c', description: '', initial_task: 't', expected_security_outcome: expected, ground_truth_label: label, file: 'f' });

describe('conditionResult', () => {
  it('takes the strongest Policy Engine decision and its non-ALLOW reasons', () => {
    const c = conditionResult(summary(), [
      ev({ event_type: 'workflow.started' }),
      ev({ event_type: 'resource.policy_decided', policy_decision: 'ALLOW', reason_code: 'AUTHORIZED_RESOURCE_OPERATION' }),
      ev({ event_type: 'message.policy_decided', policy_decision: 'BLOCK', reason_code: 'THREAT_PROMPT_INJECTION' }),
      ev({ event_type: 'message.blocked', policy_decision: 'BLOCK', reason_code: 'THREAT_PROMPT_INJECTION' }),
      ev({ event_type: 'workflow.completed' }),
    ]);
    expect(c.strongestDecision).toBe('BLOCK');
    expect(c.reasons).toEqual(['THREAT_PROMPT_INJECTION']);
    expect(c.decisionCount).toBe(2); // only *.policy_decided events count as decisions
    expect(c.durationMs).toBeGreaterThan(0);
  });

  it('reports no decision for a baseline run that bypassed the Policy Engine', () => {
    const c = conditionResult(summary({ enable_trsm: false }), [ev({ event_type: 'message.delivered', policy_decision: 'ALLOW', reason_code: 'BASELINE_BYPASS' })]);
    expect(c.strongestDecision).toBeNull();
    expect(c.decisionCount).toBe(0);
  });
});

describe('matchesExpected', () => {
  const c = (d: PolicyDecisionEnum | null, status = 'completed') => ({ summary: summary({ status }), strongestDecision: d, reasons: [], decisionCount: d ? 1 : 0, durationMs: 1 });
  it('compares the strongest decision with the expected outcome', () => {
    expect(matchesExpected('BLOCK', c('BLOCK'))).toBe(true);
    expect(matchesExpected('BLOCK', c('QUARANTINE'))).toBe(false);
    expect(matchesExpected('ALLOW', c('ALLOW'))).toBe(true);
  });
  it('treats "no decision" as ALLOW only if the run completed', () => {
    expect(matchesExpected('ALLOW', c(null))).toBe(true);
    expect(matchesExpected('ALLOW', c(null, 'failed'))).toBe(false);
    expect(matchesExpected('BLOCK', c(null))).toBe(false);
  });
});

describe('summarizeTrials', () => {
  const trial = (label: 'benign' | 'adversarial', expected: PolicyDecisionEnum, base: PolicyDecisionEnum | null, prot: PolicyDecisionEnum | null, bMs: number, pMs: number): TrialResult => {
    const mk = (d: PolicyDecisionEnum | null, ms: number) => ({ summary: summary(), strongestDecision: d, reasons: [], decisionCount: 1, durationMs: ms });
    const protectedRun = mk(prot, pMs);
    return { scenario: scenario(label, expected), baseline: mk(base, bMs), protectedRun, comparison: null, comparisonError: null, matchesExpected: matchesExpected(expected, protectedRun) };
  };

  it('counts only what was observed', () => {
    const s = summarizeTrials([
      trial('benign', 'ALLOW', null, 'ALLOW', 2, 4),
      trial('benign', 'ALLOW', null, 'BLOCK', 2, 6),
      trial('adversarial', 'BLOCK', null, 'BLOCK', 1, 3),
      trial('adversarial', 'BLOCK', null, 'ALLOW', 3, 5),
    ]);
    expect(s).toMatchObject({ trials: 4, matched: 2, adversarial: 2, adversarialStoppedProtected: 1, adversarialStoppedBaseline: 0, benign: 2, benignFlaggedProtected: 1 });
    expect(s.medianBaselineMs).toBe(2);
    expect(s.medianProtectedMs).toBe(4.5);
  });

  it('handles an empty set without dividing by zero', () => {
    expect(summarizeTrials([])).toMatchObject({ trials: 0, medianBaselineMs: null });
    expect(ratio(0, 0)).toBe('none run');
    expect(median([])).toBeNull();
  });
});
