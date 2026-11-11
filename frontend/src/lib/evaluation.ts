/**
 * Baseline-vs-protected comparison built only from what the backend returned for
 * each run. This module deliberately does NOT compute ASR/FPR/FNR: those need the
 * scenario's "adversarial objective achieved" ground truth, which the HTTP API does
 * not expose (they are produced offline by scripts/run_evaluation.py).
 */

import { AuditEvent, PolicyDecisionEnum, RunComparison, RunSummary } from '../types';
import { runTiming } from './runState';
import type { Scenario } from './scenarios';

/** Events that carry the Policy Engine's decision for a message or resource action. */
const DECISION_EVENTS = new Set(['message.policy_decided', 'resource.policy_decided']);
const RANK: Record<PolicyDecisionEnum, number> = { ALLOW: 0, REVIEW: 1, QUARANTINE: 2, BLOCK: 3 };

export interface ConditionResult {
  summary: RunSummary;
  /** Strongest decision the Policy Engine emitted; null if it made no decision (e.g. baseline bypass). */
  strongestDecision: PolicyDecisionEnum | null;
  /** Non-ALLOW reason codes, in order of first appearance. */
  reasons: string[];
  decisionCount: number;
  /** Wall-clock from workflow.started to workflow.completed audit timestamps. */
  durationMs: number | null;
}

export interface TrialResult {
  scenario: Scenario;
  baseline: ConditionResult;
  protectedRun: ConditionResult;
  comparison: RunComparison | null;
  comparisonError: string | null;
  /** Did the protected run's strongest decision equal the scenario's expected_security_outcome? */
  matchesExpected: boolean;
}

export function conditionResult(summary: RunSummary, events: AuditEvent[]): ConditionResult {
  let strongest: PolicyDecisionEnum | null = null;
  const reasons: string[] = [];
  let decisionCount = 0;
  for (const e of events) {
    if (!DECISION_EVENTS.has(e.event_type) || !e.policy_decision) continue;
    decisionCount += 1;
    if (strongest === null || RANK[e.policy_decision] > RANK[strongest]) strongest = e.policy_decision;
    if (e.policy_decision !== 'ALLOW' && e.reason_code && !reasons.includes(e.reason_code)) reasons.push(e.reason_code);
  }
  return { summary, strongestDecision: strongest, reasons, decisionCount, durationMs: runTiming(events).durationMs };
}

/**
 * The protected run "matches" when its strongest decision equals the expected outcome.
 * A run with no decisions only matches an expected ALLOW if it still completed.
 */
export function matchesExpected(expected: PolicyDecisionEnum, protectedRun: ConditionResult): boolean {
  if (protectedRun.strongestDecision === null) return expected === 'ALLOW' && protectedRun.summary.status === 'completed';
  return protectedRun.strongestDecision === expected;
}

export const median = (xs: number[]): number | null => {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};

const stopped = (d: PolicyDecisionEnum | null) => d === 'BLOCK' || d === 'QUARANTINE' || d === 'REVIEW';

export interface SuiteSummary {
  trials: number;
  matched: number;
  adversarial: number;
  /** Adversarial scenarios where the protected run produced BLOCK/QUARANTINE/REVIEW. */
  adversarialStoppedProtected: number;
  /** Adversarial scenarios where the baseline run produced any non-ALLOW decision. */
  adversarialStoppedBaseline: number;
  benign: number;
  /** Benign scenarios where the protected run produced any non-ALLOW decision. */
  benignFlaggedProtected: number;
  medianBaselineMs: number | null;
  medianProtectedMs: number | null;
}

/** Plain counts over completed trials. Not ASR/FPR: no claim is made about attack success. */
export function summarizeTrials(trials: TrialResult[]): SuiteSummary {
  const adv = trials.filter((t) => t.scenario.ground_truth_label === 'adversarial');
  const ben = trials.filter((t) => t.scenario.ground_truth_label === 'benign');
  const durations = (pick: (t: TrialResult) => number | null) => trials.map(pick).filter((x): x is number => x !== null);
  return {
    trials: trials.length,
    matched: trials.filter((t) => t.matchesExpected).length,
    adversarial: adv.length,
    adversarialStoppedProtected: adv.filter((t) => stopped(t.protectedRun.strongestDecision)).length,
    adversarialStoppedBaseline: adv.filter((t) => stopped(t.baseline.strongestDecision)).length,
    benign: ben.length,
    benignFlaggedProtected: ben.filter((t) => stopped(t.protectedRun.strongestDecision)).length,
    medianBaselineMs: median(durations((t) => t.baseline.durationMs)),
    medianProtectedMs: median(durations((t) => t.protectedRun.durationMs)),
  };
}

/** "3/4" style ratio text that never divides by zero. */
export const ratio = (n: number, d: number) => (d === 0 ? 'none run' : `${n}/${d}`);
