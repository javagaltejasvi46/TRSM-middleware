import { describe, expect, it } from 'vitest';
import { runPreChecks, validateNodeFields } from './workflowChecks';
import { defaultWorkflow } from './workflowGraph';
import { AgentNodeConfig } from '../types';

const node = (over: Partial<AgentNodeConfig> = {}): AgentNodeConfig => ({ ...defaultWorkflow().nodes[0], ...over });

describe('runPreChecks', () => {
  it('passes the default workflow', () => {
    expect(runPreChecks(defaultWorkflow())).toEqual({ errors: [], warnings: [] });
  });

  it('flags an empty workflow and a missing entry node', () => {
    const empty = runPreChecks({ ...defaultWorkflow(), nodes: [], entry_node_id: '' });
    expect(empty.errors).toEqual(expect.arrayContaining(['Add at least one agent node.', 'Choose an entry node.']));
    const missing = runPreChecks({ ...defaultWorkflow(), entry_node_id: 'nope' });
    expect(missing.errors.join(' ')).toMatch(/Entry node "nope"/);
  });

  it('flags duplicate node IDs', () => {
    const wf = defaultWorkflow();
    wf.nodes[2] = { ...wf.nodes[2], node_id: 'backend_agent' };
    expect(runPreChecks(wf).errors.join(' ')).toMatch(/used more than once/);
  });

  it('warns about peers outside the workflow and unregistered tools', () => {
    const wf = defaultWorkflow();
    wf.nodes[0] = { ...wf.nodes[0], allowed_peers: ['ghost'], allowed_tools: ['shell_exec'] };
    const { errors, warnings } = runPreChecks(wf);
    expect(errors).toEqual([]);
    expect(warnings.join(' ')).toMatch(/peer "ghost"/);
    expect(warnings.join(' ')).toMatch(/tool "shell_exec" is not registered/);
  });
});

describe('validateNodeFields (mirrors backend AgentNodeConfig)', () => {
  it('accepts a valid node', () => {
    expect(validateNodeFields(node(), [])).toEqual({});
  });

  it('requires node_id and name, and rejects a taken node_id', () => {
    expect(validateNodeFields(node({ node_id: ' ', name: '' }), [])).toMatchObject({ node_id: expect.any(String), name: expect.any(String) });
    expect(validateNodeFields(node(), ['backend_agent']).node_id).toMatch(/already uses/);
  });

  it.each([
    ['timeout_seconds', 0],
    ['timeout_seconds', 301],
    ['timeout_seconds', 2.5],
    ['call_limit', 0],
    ['call_limit', 101],
    ['call_limit', NaN],
  ] as const)('rejects %s = %s', (key, value) => {
    expect(validateNodeFields(node({ [key]: value }), [])[key]).toMatch(/whole number/);
  });

  it('accepts the boundary values', () => {
    expect(validateNodeFields(node({ timeout_seconds: 1, call_limit: 100 }), [])).toEqual({});
    expect(validateNodeFields(node({ timeout_seconds: 300, call_limit: 1 }), [])).toEqual({});
  });
});
