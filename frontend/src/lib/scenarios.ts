/**
 * Benchmark scenarios, read from the repository's versioned scenarios/ folder at
 * build time (single source of truth; the frontend keeps no copy of them).
 */

import { PolicyDecisionEnum } from '../types';

export interface Scenario {
  id: string;
  name: string;
  category: string;
  description: string;
  initial_task: string;
  expected_security_outcome: PolicyDecisionEnum;
  ground_truth_label: 'benign' | 'adversarial';
  adversarial_objective_achieved_if?: string;
  /** Path relative to scenarios/, for traceability. */
  file: string;
}

const DECISIONS: PolicyDecisionEnum[] = ['ALLOW', 'BLOCK', 'QUARANTINE', 'REVIEW'];

export type ScenarioParse = { ok: true; scenario: Scenario } | { ok: false; file: string; error: string };

/**
 * Validate one scenario file's parsed data (YAML is parsed at build time; a parse
 * failure arrives as `{ __parseError }`). Malformed files are reported, never skipped.
 */
export function parseScenario(file: string, data: unknown): ScenarioParse {
  const raw = data as any;
  if (raw && typeof raw === 'object' && typeof raw.__parseError === 'string') {
    return { ok: false, file, error: `invalid YAML: ${raw.__parseError}` };
  }
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return { ok: false, file, error: 'not a YAML mapping' };
  const missing = ['id', 'name', 'category', 'initial_task', 'expected_security_outcome', 'ground_truth_label'].filter(
    (k) => typeof raw?.[k] !== 'string' || !raw[k].trim(),
  );
  if (missing.length) return { ok: false, file, error: `missing or empty: ${missing.join(', ')}` };
  if (!DECISIONS.includes(raw.expected_security_outcome)) {
    return { ok: false, file, error: `expected_security_outcome "${raw.expected_security_outcome}" is not ALLOW/BLOCK/QUARANTINE/REVIEW` };
  }
  if (raw.ground_truth_label !== 'benign' && raw.ground_truth_label !== 'adversarial') {
    return { ok: false, file, error: `ground_truth_label "${raw.ground_truth_label}" is not benign/adversarial` };
  }
  return {
    ok: true,
    scenario: {
      id: raw.id,
      name: raw.name,
      category: raw.category,
      description: typeof raw.description === 'string' ? raw.description : '',
      initial_task: raw.initial_task,
      expected_security_outcome: raw.expected_security_outcome,
      ground_truth_label: raw.ground_truth_label,
      adversarial_objective_achieved_if: typeof raw.adversarial_objective_achieved_if === 'string' ? raw.adversarial_objective_achieved_if : undefined,
      file,
    },
  };
}

export function loadScenarios(files: Record<string, unknown>): { scenarios: Scenario[]; errors: { file: string; error: string }[] } {
  const scenarios: Scenario[] = [];
  const errors: { file: string; error: string }[] = [];
  for (const [path, data] of Object.entries(files)) {
    const file = path.replace(/^.*?scenarios\//, '');
    const r = parseScenario(file, data);
    if (r.ok) scenarios.push(r.scenario);
    else errors.push({ file: r.file, error: r.error });
  }
  // Benign controls first, then adversarial, each by id — stable order for tables.
  scenarios.sort((a, b) => (a.ground_truth_label === b.ground_truth_label ? a.id.localeCompare(b.id) : a.ground_truth_label === 'benign' ? -1 : 1));
  return { scenarios, errors };
}
