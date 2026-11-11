/**
 * Client-side pre-checks. These only catch obvious mistakes before a request is
 * sent; they are NOT validation results. `POST /api/workflows/validate` and the
 * backend gateways are authoritative.
 */

import { AgentNodeConfig, WorkflowConfig } from '../types';
import { AGENT_ROLES, KNOWN_TOOLS, LIMITS } from './workflowGraph';

export interface PreCheckResult {
  errors: string[];
  warnings: string[];
}

export function runPreChecks(wf: WorkflowConfig): PreCheckResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const ids = wf.nodes.map((n) => n.node_id);
  const idSet = new Set(ids);

  if (wf.nodes.length === 0) errors.push('Add at least one agent node.');
  if (!wf.entry_node_id) errors.push('Choose an entry node.');
  else if (!idSet.has(wf.entry_node_id)) errors.push(`Entry node "${wf.entry_node_id}" is not on the canvas.`);

  const seen = new Set<string>();
  for (const id of ids) {
    if (!id.trim()) errors.push('A node has an empty node ID.');
    else if (seen.has(id)) errors.push(`Node ID "${id}" is used more than once.`);
    seen.add(id);
  }

  for (const n of wf.nodes) {
    for (const issue of Object.values(validateNodeFields(n, ids.filter((x) => x !== n.node_id)))) {
      if (issue) errors.push(`${n.node_id || '(unnamed)'}: ${issue}`);
    }
    for (const peer of n.allowed_peers) {
      if (!idSet.has(peer)) warnings.push(`${n.node_id}: allowed peer "${peer}" is not in this workflow.`);
    }
    for (const tool of n.allowed_tools) {
      if (!KNOWN_TOOLS.includes(tool)) warnings.push(`${n.node_id}: tool "${tool}" is not registered in the backend tool registry and will be blocked.`);
    }
  }
  return { errors, warnings };
}

export type NodeFieldErrors = Partial<Record<'node_id' | 'name' | 'role' | 'timeout_seconds' | 'call_limit', string>>;

/** Field rules mirrored from AgentNodeConfig (backend/app/schemas/agent.py). */
export function validateNodeFields(node: AgentNodeConfig, otherIds: string[]): NodeFieldErrors {
  const errs: NodeFieldErrors = {};
  if (!node.node_id.trim()) errs.node_id = 'Node ID is required.';
  else if (otherIds.includes(node.node_id)) errs.node_id = `Another node already uses "${node.node_id}".`;
  if (!node.name.trim()) errs.name = 'Name is required.';
  if (!AGENT_ROLES.includes(node.role)) errs.role = 'Choose a role.';
  for (const key of ['timeout_seconds', 'call_limit'] as const) {
    const v = node[key];
    const { min, max } = LIMITS[key];
    if (!Number.isInteger(v) || v < min || v > max) errs[key] = `Enter a whole number from ${min} to ${max}.`;
  }
  return errs;
}
