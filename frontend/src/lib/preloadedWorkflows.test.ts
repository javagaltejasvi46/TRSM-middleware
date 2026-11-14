import { describe, expect, it } from 'vitest';
import { PRELOADED_WORKFLOWS } from './preloadedWorkflows';
import { runPreChecks } from './workflowChecks';

describe('preloadedWorkflows', () => {
  it('contains at least 5 distinct preloaded workflows', () => {
    expect(PRELOADED_WORKFLOWS.length).toBeGreaterThanOrEqual(5);
    const ids = new Set(PRELOADED_WORKFLOWS.map((w) => w.id));
    expect(ids.size).toBe(PRELOADED_WORKFLOWS.length);
  });

  it('every preloaded workflow passes runPreChecks with 0 errors', () => {
    for (const item of PRELOADED_WORKFLOWS) {
      const { errors } = runPreChecks(item.workflow);
      expect(errors, `Workflow ${item.id} had precheck errors: ${errors.join(', ')}`).toEqual([]);
      expect(item.defaultTask.length).toBeGreaterThan(5);
      expect(item.workflow.entry_node_id).toBeTruthy();
      expect(item.workflow.nodes.length).toBeGreaterThanOrEqual(2);
    }
  });

  it('includes attack workflows covering prompt injection, memory poisoning, role hijacking, and resource authorization', () => {
    const categories = new Set(PRELOADED_WORKFLOWS.map((w) => w.category));
    expect(categories.has('benign')).toBe(true);
    expect(categories.has('prompt_injection')).toBe(true);
    expect(categories.has('memory_poisoning')).toBe(true);
    expect(categories.has('role_hijacking')).toBe(true);
    expect(categories.has('resource_authorization')).toBe(true);
  });
});

