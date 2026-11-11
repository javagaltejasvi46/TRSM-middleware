import React, { useMemo, useRef, useState } from 'react';
import { AlertCircle, CheckCircle2, ChevronDown, ChevronRight, FlaskConical, Info, Loader2, Play, Square, XCircle } from 'lucide-react';
import { runsApi } from '../api/runs';
import { eventsApi } from '../api/events';
import { metricsApi } from '../api/metrics';
import { ApiError } from '../api/client';
import { MetricResult } from '../types';
import { DecisionBadge } from '../components/DecisionBadge/DecisionBadge';
import { SCENARIO_FILES } from '../lib/scenarioFiles';
import { loadScenarios, type Scenario } from '../lib/scenarios';
import { conditionResult, matchesExpected, ratio, summarizeTrials, type ConditionResult, type TrialResult } from '../lib/evaluation';
import { formatMs } from '../lib/runState';
import { BLOCKED_ATTACKS_NOTE, OVERHEAD_FIELD_NOTE, PLACEHOLDER_METRIC_FIELDS, ZERO_DENOMINATOR_NOTE } from '../lib/backendCaveats';

type RowState = { kind: 'idle' } | { kind: 'running'; step: string } | { kind: 'error'; message: string } | { kind: 'done'; trial: TrialResult };

const errorText = (e: unknown) => (e instanceof ApiError ? e.message : (e as Error)?.message ?? String(e));

/** Run one scenario twice through the real API (baseline, then protected) and compare. */
async function runTrial(s: Scenario, onStep: (step: string) => void): Promise<TrialResult> {
  const one = async (enable_trsm: boolean): Promise<ConditionResult> => {
    onStep(enable_trsm ? 'protected run…' : 'baseline run…');
    const summary = await runsApi.start({ task: s.initial_task, enable_trsm });
    const events = await eventsApi.getEvents(summary.run_id);
    return conditionResult(summary, events);
  };
  const baseline = await one(false);
  const protectedRun = await one(true);
  onStep('comparing…');
  let comparison = null;
  let comparisonError = null;
  try {
    comparison = await metricsApi.compareRuns(baseline.summary.run_id, protectedRun.summary.run_id);
  } catch (e) {
    comparisonError = errorText(e);
  }
  return { scenario: s, baseline, protectedRun, comparison, comparisonError, matchesExpected: matchesExpected(s.expected_security_outcome, protectedRun) };
}

const metricText = (m: MetricResult) => {
  if (!m.available) return `Not available${m.unavailable_reason ? `: ${m.unavailable_reason}` : ''}`;
  if (m.denominator === 0) return `n/a (${ZERO_DENOMINATOR_NOTE})`;
  const pct = m.value == null ? '—' : `${(m.value * 100).toFixed(1)}%`;
  return m.numerator != null && m.denominator != null ? `${pct} (${m.numerator}/${m.denominator})` : pct;
};

const Card: React.FC<{ title: string; children: React.ReactNode; id?: string }> = ({ title, children, id }) => (
  <section className="surface" aria-labelledby={id} style={{ padding: '16px 18px' }}>
    <h2 id={id} style={{ fontSize: '15px', fontWeight: 700, marginBottom: '10px' }}>{title}</h2>
    {children}
  </section>
);

const Tile: React.FC<{ label: string; value: string; note: string }> = ({ label, value, note }) => (
  <div className="well" style={{ padding: '12px 14px', background: 'linear-gradient(180deg, #ffffff 0%, var(--surface-sunken) 100%)' }}>
    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>{label}</div>
    <div style={{ fontSize: '22px', fontWeight: 700, letterSpacing: '-0.02em', margin: '2px 0' }}>{value}</div>
    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{note}</div>
  </div>
);

const th: React.CSSProperties = { textAlign: 'left', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', padding: '8px 10px', borderBottom: '1px solid var(--border-strong)', whiteSpace: 'nowrap' };
const td: React.CSSProperties = { fontSize: '12px', padding: '10px', borderBottom: '1px solid var(--border-color)', verticalAlign: 'top' };

const Condition: React.FC<{ c: ConditionResult }> = ({ c }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-start' }}>
    <DecisionBadge decision={c.strongestDecision} noneLabel={c.summary.enable_trsm ? 'No decision' : 'No decision (TRSM off)'} />
    <span style={{ color: 'var(--text-secondary)' }}>
      {c.summary.blocked_actions} blocked · {c.summary.status}
    </span>
    {c.reasons.map((r) => (
      <span key={r} style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', overflowWrap: 'anywhere' }}>{r}</span>
    ))}
  </div>
);

export const EvaluationPage: React.FC = () => {
  const { scenarios, errors: loadErrors } = useMemo(() => loadScenarios(SCENARIO_FILES), []);
  const [rows, setRows] = useState<Record<string, RowState>>({});
  const [suiteRunning, setSuiteRunning] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const stopRequested = useRef(false);

  const setRow = (id: string, r: RowState) => setRows((cur) => ({ ...cur, [id]: r }));
  const done = scenarios.map((s) => rows[s.id]).filter((r): r is Extract<RowState, { kind: 'done' }> => r?.kind === 'done').map((r) => r.trial);
  const summary = summarizeTrials(done);
  const busy = suiteRunning || Object.values(rows).some((r) => r.kind === 'running');

  const runOne = async (s: Scenario) => {
    setRow(s.id, { kind: 'running', step: 'starting…' });
    try {
      setRow(s.id, { kind: 'done', trial: await runTrial(s, (step) => setRow(s.id, { kind: 'running', step })) });
    } catch (e) {
      setRow(s.id, { kind: 'error', message: errorText(e) });
    }
  };

  const runAll = async () => {
    stopRequested.current = false;
    setSuiteRunning(true);
    for (const s of scenarios) {
      if (stopRequested.current) break;
      await runOne(s);
    }
    setSuiteRunning(false);
  };

  const progress = suiteRunning ? `Running scenario ${Math.min(done.length + 1, scenarios.length)} of ${scenarios.length}…` : null;

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 style={{ fontSize: '22px', fontWeight: 700, letterSpacing: '-0.02em' }}>Baseline vs. TRSM-Protected Evaluation</h1>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: 900 }}>
          Each scenario from the repository&apos;s <code>scenarios/</code> folder is run twice against the live backend: once with TRSM off (baseline) and once with it on.
          Everything shown is what those runs returned. Nothing here is precomputed or typed in.
        </p>
      </div>

      {loadErrors.length > 0 && (
        <div role="alert" className="badge-block" style={{ borderRadius: 10, padding: '10px 12px', fontSize: '12px' }}>
          <strong>Some scenario files could not be read and are not included:</strong>
          <ul style={{ marginLeft: 18 }}>{loadErrors.map((e) => <li key={e.file}>{e.file}: {e.error}</li>)}</ul>
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        <button type="button" className="btn btn-primary" onClick={runAll} disabled={busy || scenarios.length === 0} style={{ minHeight: 42 }}>
          {suiteRunning ? <Loader2 size={16} className="animate-spin" aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
          Run all {scenarios.length} scenarios
        </button>
        {suiteRunning && (
          <button type="button" className="btn btn-secondary" onClick={() => (stopRequested.current = true)}>
            <Square size={14} aria-hidden="true" /> Stop after current
          </button>
        )}
        <span role="status" style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          {progress ?? (done.length ? `${done.length} of ${scenarios.length} scenarios have results.` : 'No scenarios run yet.')}
        </span>
      </div>

      <Card title={`Summary of ${done.length} completed trial${done.length === 1 ? '' : 's'}`} id="eval-summary">
        {done.length === 0 ? (
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>No results yet. Run the scenarios to see counts from real runs.</p>
        ) : (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              <Tile label="Protected decision matched expected" value={ratio(summary.matched, summary.trials)} note="vs. expected_security_outcome in each scenario file" />
              <Tile label="Adversarial stopped (TRSM on)" value={ratio(summary.adversarialStoppedProtected, summary.adversarial)} note="protected run produced BLOCK, QUARANTINE or REVIEW" />
              <Tile label="Adversarial stopped (TRSM off)" value={ratio(summary.adversarialStoppedBaseline, summary.adversarial)} note="baseline run produced any non-ALLOW decision" />
              <Tile label="Benign flagged (TRSM on)" value={ratio(summary.benignFlaggedProtected, summary.benign)} note="benign scenario got a non-ALLOW decision" />
              <Tile
                label="Median run duration"
                value={`${formatMs(summary.medianBaselineMs)} → ${formatMs(summary.medianProtectedMs)}`}
                note={`baseline → protected, n=${summary.trials}, from audit timestamps`}
              />
            </div>
            <p style={{ display: 'flex', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)', marginTop: '10px' }}>
              <Info size={13} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} />
              These are plain counts from the runs above, with mock agents on one machine. They are not ASR/FPR (see "Not available" below), and durations from a
              handful of runs are not a latency benchmark.
            </p>
          </>
        )}
      </Card>

      <Card title="Scenario trials" id="eval-trials">
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 980 }}>
            <thead>
              <tr>
                <th scope="col" style={th}>Scenario</th>
                <th scope="col" style={th}>Label</th>
                <th scope="col" style={th}>Expected</th>
                <th scope="col" style={th}>Baseline (TRSM off)</th>
                <th scope="col" style={th}>Protected (TRSM on)</th>
                <th scope="col" style={th}>Matches expected</th>
                <th scope="col" style={th}>Duration</th>
                <th scope="col" style={th}><span style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)' }}>Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((s) => {
                const r = rows[s.id] ?? { kind: 'idle' };
                const t = r.kind === 'done' ? r.trial : null;
                const isOpen = expanded === s.id && t;
                return (
                  <React.Fragment key={s.id}>
                    <tr>
                      <td style={td}>
                        <div style={{ fontWeight: 600 }}>{s.name}</div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)' }}>{s.id}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 2, maxWidth: 260, overflowWrap: 'anywhere' }} title={s.initial_task}>
                          “{s.initial_task.length > 90 ? `${s.initial_task.slice(0, 90)}…` : s.initial_task}”
                        </div>
                      </td>
                      <td style={td}>
                        <span className={`badge ${s.ground_truth_label === 'benign' ? 'badge-allow' : 'badge-quarantine'}`}>{s.ground_truth_label}</span>
                        {s.category !== s.ground_truth_label && <div style={{ color: 'var(--text-secondary)', marginTop: 4 }}>{s.category.replace(/_/g, ' ')}</div>}
                      </td>
                      <td style={td}><DecisionBadge decision={s.expected_security_outcome} /></td>
                      <td style={td}>{t ? <Condition c={t.baseline} /> : <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                      <td style={td}>{t ? <Condition c={t.protectedRun} /> : <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                      <td style={td}>
                        {t ? (
                          t.matchesExpected ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--ok-text)', fontWeight: 600 }}>
                              <CheckCircle2 size={14} aria-hidden="true" /> Matches
                            </span>
                          ) : (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--error-text)', fontWeight: 600 }}>
                              <XCircle size={14} aria-hidden="true" /> Differs
                            </span>
                          )
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </td>
                      <td style={{ ...td, fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                        {t ? `${formatMs(t.baseline.durationMs)} → ${formatMs(t.protectedRun.durationMs)}` : '—'}
                      </td>
                      <td style={{ ...td, whiteSpace: 'nowrap', textAlign: 'right' }}>
                        {r.kind === 'running' ? (
                          <span role="status" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--accent-text)' }}>
                            <Loader2 size={14} className="animate-spin" aria-hidden="true" /> {r.step}
                          </span>
                        ) : (
                          <span style={{ display: 'inline-flex', gap: 6 }}>
                            {t && (
                              <button
                                type="button"
                                className="btn btn-secondary"
                                style={{ minHeight: 30, padding: '2px 8px' }}
                                aria-expanded={Boolean(isOpen)}
                                aria-controls={`eval-detail-${s.id}`}
                                onClick={() => setExpanded(isOpen ? null : s.id)}
                              >
                                {isOpen ? <ChevronDown size={13} aria-hidden="true" /> : <ChevronRight size={13} aria-hidden="true" />} Details
                              </button>
                            )}
                            <button type="button" className="btn btn-secondary" style={{ minHeight: 30, padding: '2px 8px' }} onClick={() => runOne(s)} disabled={busy} aria-label={`Run ${s.id}`}>
                              <Play size={13} aria-hidden="true" /> {t || r.kind === 'error' ? 'Re-run' : 'Run'}
                            </button>
                          </span>
                        )}
                      </td>
                    </tr>
                    {r.kind === 'error' && (
                      <tr>
                        <td colSpan={8} style={{ ...td, paddingTop: 0 }}>
                          <div role="alert" className="badge-block" style={{ display: 'flex', gap: 6, borderRadius: 8, padding: '6px 10px' }}>
                            <AlertCircle size={13} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} /> Trial failed, no result recorded: {r.message}
                          </div>
                        </td>
                      </tr>
                    )}
                    {isOpen && t && (
                      <tr id={`eval-detail-${s.id}`}>
                        <td colSpan={8} style={{ ...td, background: 'var(--surface-sunken)' }}>
                          <TrialDetail t={t} />
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '20px', alignItems: 'start' }}>
        <Card title="Not available from the API" id="eval-unavailable">
          <ul style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px', marginLeft: 18 }}>
            <li>
              <strong>Attack Success Rate, False Positive Rate, False Negative Rate.</strong> These need to know whether each attack&apos;s objective was achieved.
              They are computed offline by <code>scripts/run_evaluation.py</code> (<code>backend/app/evaluation/runner.py</code>) and are not exposed over HTTP, so this
              page does not show them.
            </li>
            <li>
              <strong>Latency (mean, p95) and task success from the metrics API.</strong> avg_latency_ms is {PLACEHOLDER_METRIC_FIELDS.avg_latency_ms}; p95_latency_ms is{' '}
              {PLACEHOLDER_METRIC_FIELDS.p95_latency_ms}; task_success is {PLACEHOLDER_METRIC_FIELDS.task_success}. The durations above are measured from audit
              timestamps instead.
            </li>
            <li>
              <strong>overhead_ms from the comparison API.</strong> It is {OVERHEAD_FIELD_NOTE}.
            </li>
            <li>
              <strong>Token overhead.</strong> Not recorded by the backend.
            </li>
          </ul>
        </Card>

        <Card title="Metric definitions" id="eval-definitions">
          <dl style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
            {[
              ['CSS (Component Synergy Score)', 'As computed by backend/app/evaluation/metrics/css.py: delivered inter-agent messages ÷ proposed messages for the run.'],
              ['TUE (Tool Utilization Efficacy)', 'Authorized, successful tool operations ÷ total proposed tool operations (docs/evaluation/metric-definitions.md). The backend counts resource.executed ÷ resource.proposed events (tue.py).'],
              ['ASR (Attack Success Rate)', 'Successful attack trials ÷ total attack trials; an attack succeeds only if its adversarial objective is achieved (metric-definitions.md). Offline only.'],
              ['FPR / FNR', 'Benign actions wrongly blocked ÷ legitimate benign actions; adversarial actions wrongly allowed ÷ adversarial actions (metric-definitions.md). Offline only.'],
              ['Matches expected', 'This page only: the protected run’s strongest Policy Engine decision equals the scenario file’s expected_security_outcome.'],
            ].map(([k, v]) => (
              <div key={k}>
                <dt style={{ fontWeight: 600 }}>{k}</dt>
                <dd style={{ color: 'var(--text-secondary)' }}>{v}</dd>
              </div>
            ))}
          </dl>
        </Card>
      </div>
    </div>
  );
};

const TrialDetail: React.FC<{ t: TrialResult }> = ({ t }) => {
  const c = t.comparison;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '12px', fontSize: '12px' }}>
      <div>
        <div style={{ fontWeight: 600, marginBottom: 4 }}>Runs</div>
        <div>Baseline: <code>{t.baseline.summary.run_id}</code></div>
        <div>Protected: <code>{t.protectedRun.summary.run_id}</code></div>
        <div style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
          Policy decisions: baseline {t.baseline.decisionCount}, protected {t.protectedRun.decisionCount}. Workflow: backend default (no workflow sent). Source: <code>scenarios/{t.scenario.file}</code>
        </div>
        {t.scenario.adversarial_objective_achieved_if && (
          <div style={{ color: 'var(--text-secondary)', marginTop: 4 }}>Attack objective (not checked here): {t.scenario.adversarial_objective_achieved_if}</div>
        )}
      </div>
      <div>
        <div style={{ fontWeight: 600, marginBottom: 4 }}>From /api/evaluations/compare</div>
        {t.comparisonError ? (
          <div role="alert" style={{ color: 'var(--error-text)' }}>Comparison unavailable: {t.comparisonError}</div>
        ) : c ? (
          <table style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th scope="col" style={{ ...th, padding: '2px 8px 2px 0', borderBottom: 'none' }}>Metric</th>
                <th scope="col" style={{ ...th, padding: '2px 8px', borderBottom: 'none' }}>Baseline</th>
                <th scope="col" style={{ ...th, padding: '2px 8px', borderBottom: 'none' }}>Protected</th>
              </tr>
            </thead>
            <tbody>
              <tr><th scope="row" style={{ textAlign: 'left', fontWeight: 500, paddingRight: 8 }}>CSS</th><td style={{ padding: '2px 8px' }}>{metricText(c.baseline_metrics.css)}</td><td style={{ padding: '2px 8px' }}>{metricText(c.protected_metrics.css)}</td></tr>
              <tr><th scope="row" style={{ textAlign: 'left', fontWeight: 500, paddingRight: 8 }}>TUE</th><td style={{ padding: '2px 8px' }}>{metricText(c.baseline_metrics.tue)}</td><td style={{ padding: '2px 8px' }}>{metricText(c.protected_metrics.tue)}</td></tr>
              <tr>
                <th scope="row" style={{ textAlign: 'left', fontWeight: 500, paddingRight: 8 }} title={BLOCKED_ATTACKS_NOTE}>Non-ALLOW decision events*</th>
                <td style={{ padding: '2px 8px' }}>{c.baseline_metrics.security_blocked_attacks}</td>
                <td style={{ padding: '2px 8px' }}>{c.protected_metrics.security_blocked_attacks}</td>
              </tr>
            </tbody>
          </table>
        ) : null}
        {c && <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>* security_blocked_attacks {BLOCKED_ATTACKS_NOTE}.</div>}
      </div>
    </div>
  );
};
