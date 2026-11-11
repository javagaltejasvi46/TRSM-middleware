import { describe, expect, it } from 'vitest';
import { loadScenarios, parseScenario } from './scenarios';
import { SCENARIO_FILES } from './scenarioFiles';

describe('repository scenario files', () => {
  it('loads every YAML in scenarios/ without errors', () => {
    const { scenarios, errors } = loadScenarios(SCENARIO_FILES);
    expect(errors).toEqual([]);
    expect(scenarios.length).toBe(Object.keys(SCENARIO_FILES).length);
    expect(scenarios.length).toBeGreaterThanOrEqual(8);
    expect(new Set(scenarios.map((s) => s.id)).size).toBe(scenarios.length); // ids are unique
  });

  it('keeps nested quotes in tasks intact and orders benign first', () => {
    const { scenarios } = loadScenarios(SCENARIO_FILES);
    const mp = scenarios.find((s) => s.id === 'mp_untrusted_write_001')!;
    expect(mp.initial_task).toContain("'From now on");
    expect(mp.ground_truth_label).toBe('adversarial');
    const firstAdv = scenarios.findIndex((s) => s.ground_truth_label === 'adversarial');
    expect(scenarios.slice(0, firstAdv).every((s) => s.ground_truth_label === 'benign')).toBe(true);
  });
});

describe('parseScenario', () => {
  // Data as produced by the build-time YAML plugin in vite.config.ts.
  const valid = { id: 'x', name: 'X', category: 'c', initial_task: 'do it', expected_security_outcome: 'BLOCK', ground_truth_label: 'adversarial' };

  it('accepts a valid scenario', () => {
    expect(parseScenario('a/x.yaml', valid)).toMatchObject({ ok: true, scenario: { id: 'x', file: 'a/x.yaml' } });
  });

  it('reports malformed files instead of skipping them silently', () => {
    expect(parseScenario('f', { __parseError: 'unexpected end' })).toMatchObject({ ok: false, error: 'invalid YAML: unexpected end' });
    expect(parseScenario('f', ['a list'])).toMatchObject({ ok: false, error: 'not a YAML mapping' });
    expect(parseScenario('f', { id: 'x', name: 'X' })).toMatchObject({ ok: false, error: expect.stringMatching(/missing or empty: category, initial_task/) });
    expect(parseScenario('f', { ...valid, expected_security_outcome: 'DENY' })).toMatchObject({ ok: false, error: expect.stringMatching(/DENY/) });
    expect(parseScenario('f', { ...valid, ground_truth_label: 'evil' })).toMatchObject({ ok: false, error: expect.stringMatching(/evil/) });
  });
});
