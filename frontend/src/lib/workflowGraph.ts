/**
 * Pure helpers for the playground's workflow model.
 *
 * The canvas edits a `WorkflowConfig` (backend/app/schemas/workflow.py). Edges and
 * `allowed_peers` are kept in sync: an edge A -> B exists exactly when B is in
 * A.allowed_peers and both nodes exist. `allowed_peers` is what the backend
 * PolicyEngine checks, so the canvas always shows the peer policy it will be asked
 * to enforce. Nothing here authorizes anything; the backend gateways decide.
 */

import { AgentNodeConfig, AgentRole, WorkflowConfig, WorkflowEdge } from '../types';

export interface XYPosition {
  x: number;
  y: number;
}

/** Key under AgentNodeConfig.metadata where the canvas stores its layout. */
export const UI_POSITION_KEY = 'ui_position';

export const AGENT_ROLES: AgentRole[] = ['backend', 'db_manager', 'qa', 'devops', 'custom'];

export const ROLE_LABELS: Record<AgentRole, string> = {
  backend: 'Backend',
  db_manager: 'DB Manager',
  qa: 'QA',
  devops: 'DevOps',
  custom: 'Custom',
};

/** Resources registered in backend/app/runtime/tool_registry.py. */
export const KNOWN_TOOLS = ['customer_db', 'workflow_memory', 'test_suite'];

/** Field bounds mirrored from AgentNodeConfig in backend/app/schemas/agent.py. */
export const LIMITS = {
  timeout_seconds: { min: 1, max: 300 },
  call_limit: { min: 1, max: 100 },
} as const;

export function getPosition(node: AgentNodeConfig): XYPosition {
  const pos = node.metadata?.[UI_POSITION_KEY];
  if (pos && typeof pos.x === 'number' && typeof pos.y === 'number') {
    return { x: pos.x, y: pos.y };
  }
  return { x: 0, y: 0 };
}

export function setPosition(node: AgentNodeConfig, position: XYPosition): AgentNodeConfig {
  return { ...node, metadata: { ...(node.metadata ?? {}), [UI_POSITION_KEY]: { x: position.x, y: position.y } } };
}

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

const overlaps = (a: Rect, b: Rect, gap: number) =>
  a.x < b.x + b.width + gap && a.x + a.width + gap > b.x && a.y < b.y + b.height + gap && a.y + a.height + gap > b.y;

/**
 * Top-left position for a new node of `size`, as close to `center` as possible
 * without overlapping any of `occupied`. Searches outward ring by ring; spots
 * outside `bounds` (e.g. the visible viewport) are skipped when bounds are given.
 */
export function findFreePosition(
  center: XYPosition,
  size: { width: number; height: number },
  occupied: Rect[],
  bounds?: Rect,
  gap = 24,
): XYPosition {
  const origin = { x: center.x - size.width / 2, y: center.y - size.height / 2 };
  const step = { x: size.width / 2 + gap, y: size.height / 2 + gap };
  const inside = (r: Rect) =>
    !bounds || (r.x >= bounds.x && r.y >= bounds.y && r.x + r.width <= bounds.x + bounds.width && r.y + r.height <= bounds.y + bounds.height);
  for (let ring = 0; ring <= 8; ring++) {
    for (let dy = -ring; dy <= ring; dy++) {
      for (let dx = -ring; dx <= ring; dx++) {
        if (Math.max(Math.abs(dx), Math.abs(dy)) !== ring) continue;
        const r = { x: origin.x + dx * step.x, y: origin.y + dy * step.y, ...size };
        if (inside(r) && !occupied.some((o) => overlaps(r, o, gap))) return { x: r.x, y: r.y };
      }
    }
  }
  return origin;
}

export function uniqueNodeId(base: string, existing: Iterable<string>): string {
  const taken = new Set(existing);
  if (!taken.has(base)) return base;
  let i = 2;
  while (taken.has(`${base}_${i}`)) i++;
  return `${base}_${i}`;
}

export function createAgentNode(role: AgentRole, existingIds: Iterable<string>, position: XYPosition): AgentNodeConfig {
  const nodeId = uniqueNodeId(`${role}_agent`, existingIds);
  return setPosition(
    {
      node_id: nodeId,
      name: `${ROLE_LABELS[role]} Agent`,
      role,
      model: 'mock',
      instructions: '',
      allowed_peers: [],
      allowed_tools: [],
      timeout_seconds: 30,
      call_limit: 10,
      metadata: {},
    },
    position,
  );
}

export function addNode(wf: WorkflowConfig, node: AgentNodeConfig): WorkflowConfig {
  return {
    ...wf,
    nodes: [...wf.nodes, node],
    entry_node_id: wf.entry_node_id || node.node_id,
  };
}

export function deleteNode(wf: WorkflowConfig, nodeId: string): WorkflowConfig {
  const nodes = wf.nodes
    .filter((n) => n.node_id !== nodeId)
    .map((n) => (n.allowed_peers.includes(nodeId) ? { ...n, allowed_peers: n.allowed_peers.filter((p) => p !== nodeId) } : n));
  const entry = wf.entry_node_id === nodeId ? nodes[0]?.node_id ?? '' : wf.entry_node_id;
  return { ...wf, nodes, entry_node_id: entry };
}

/**
 * Replace a node's configuration. If node_id changed, references in other nodes'
 * allowed_peers and the entry node are renamed too, so no route is silently lost.
 */
export function updateNode(wf: WorkflowConfig, nodeId: string, next: AgentNodeConfig): WorkflowConfig {
  const renamed = next.node_id !== nodeId;
  const nodes = wf.nodes.map((n) => {
    if (n.node_id === nodeId) return next;
    if (renamed && n.allowed_peers.includes(nodeId)) {
      return { ...n, allowed_peers: n.allowed_peers.map((p) => (p === nodeId ? next.node_id : p)) };
    }
    return n;
  });
  const entry = renamed && wf.entry_node_id === nodeId ? next.node_id : wf.entry_node_id;
  return { ...wf, nodes, entry_node_id: entry };
}

export function moveNode(wf: WorkflowConfig, nodeId: string, position: XYPosition): WorkflowConfig {
  return { ...wf, nodes: wf.nodes.map((n) => (n.node_id === nodeId ? setPosition(n, position) : n)) };
}

export function addPeer(wf: WorkflowConfig, sourceId: string, targetId: string): WorkflowConfig {
  if (sourceId === targetId) return wf;
  return {
    ...wf,
    nodes: wf.nodes.map((n) =>
      n.node_id === sourceId && !n.allowed_peers.includes(targetId)
        ? { ...n, allowed_peers: [...n.allowed_peers, targetId] }
        : n,
    ),
  };
}

export function removePeer(wf: WorkflowConfig, sourceId: string, targetId: string): WorkflowConfig {
  return {
    ...wf,
    nodes: wf.nodes.map((n) =>
      n.node_id === sourceId ? { ...n, allowed_peers: n.allowed_peers.filter((p) => p !== targetId) } : n,
    ),
  };
}

export function setEntryNode(wf: WorkflowConfig, nodeId: string): WorkflowConfig {
  return { ...wf, entry_node_id: nodeId };
}

/** Edges derived from allowed_peers; peers that are not nodes in this workflow get no edge. */
export function deriveEdges(wf: WorkflowConfig): WorkflowEdge[] {
  const ids = new Set(wf.nodes.map((n) => n.node_id));
  const edges: WorkflowEdge[] = [];
  for (const n of wf.nodes) {
    for (const peer of n.allowed_peers) {
      if (ids.has(peer)) edges.push({ source_node_id: n.node_id, target_node_id: peer, metadata: {} });
    }
  }
  return edges;
}

/** The WorkflowConfig sent to the backend or exported as JSON. */
export function toWorkflowConfig(wf: WorkflowConfig): WorkflowConfig {
  return { ...wf, edges: deriveEdges(wf) };
}

export function exportWorkflowJson(wf: WorkflowConfig): string {
  return JSON.stringify(toWorkflowConfig(wf), null, 2);
}

export type ImportResult =
  | { ok: true; workflow: WorkflowConfig; notices: string[] }
  | { ok: false; errors: string[] };

const isObject = (v: unknown): v is Record<string, any> => typeof v === 'object' && v !== null && !Array.isArray(v);
const isStringArray = (v: unknown): v is string[] => Array.isArray(v) && v.every((x) => typeof x === 'string');

/**
 * Parse an exported workflow. Shape errors reject the file (nothing is dropped
 * silently). Edges and allowed_peers are reconciled, and every peer that is added
 * because of that is reported back so the user can see the permission change.
 */
export function importWorkflowJson(text: string): ImportResult {
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch (e) {
    return { ok: false, errors: [`File is not valid JSON: ${(e as Error).message}`] };
  }
  if (!isObject(raw)) return { ok: false, errors: ['Top-level value must be a workflow object.'] };

  const errors: string[] = [];
  const notices: string[] = [];
  if (!Array.isArray(raw.nodes)) errors.push('"nodes" must be an array.');
  if (raw.edges !== undefined && !Array.isArray(raw.edges)) errors.push('"edges" must be an array if present.');
  if (errors.length) return { ok: false, errors };

  const nodes: AgentNodeConfig[] = [];
  (raw.nodes as unknown[]).forEach((n, i) => {
    const where = `nodes[${i}]`;
    if (!isObject(n)) return errors.push(`${where} must be an object.`);
    if (typeof n.node_id !== 'string') errors.push(`${where}.node_id must be a string.`);
    if (typeof n.name !== 'string') errors.push(`${where}.name must be a string.`);
    if (n.role !== undefined && !AGENT_ROLES.includes(n.role)) errors.push(`${where}.role "${n.role}" is not a known role.`);
    if (n.allowed_peers !== undefined && !isStringArray(n.allowed_peers)) errors.push(`${where}.allowed_peers must be a list of strings.`);
    if (n.allowed_tools !== undefined && !isStringArray(n.allowed_tools)) errors.push(`${where}.allowed_tools must be a list of strings.`);
    for (const key of ['timeout_seconds', 'call_limit'] as const) {
      if (n[key] !== undefined && !Number.isInteger(n[key])) errors.push(`${where}.${key} must be an integer.`);
    }
    nodes.push({
      node_id: n.node_id,
      name: n.name,
      role: n.role ?? 'custom',
      model: typeof n.model === 'string' ? n.model : 'mock',
      instructions: typeof n.instructions === 'string' ? n.instructions : '',
      allowed_peers: n.allowed_peers ?? [],
      allowed_tools: n.allowed_tools ?? [],
      timeout_seconds: n.timeout_seconds ?? 30,
      call_limit: n.call_limit ?? 10,
      metadata: isObject(n.metadata) ? n.metadata : {},
    });
  });

  const edges: WorkflowEdge[] = [];
  ((raw.edges as unknown[]) ?? []).forEach((e, i) => {
    if (!isObject(e) || typeof e.source_node_id !== 'string' || typeof e.target_node_id !== 'string') {
      errors.push(`edges[${i}] must have string source_node_id and target_node_id.`);
      return;
    }
    edges.push({ source_node_id: e.source_node_id, target_node_id: e.target_node_id, metadata: isObject(e.metadata) ? e.metadata : {} });
  });
  if (errors.length) return { ok: false, errors };

  let wf: WorkflowConfig = {
    workflow_id: typeof raw.workflow_id === 'string' && raw.workflow_id ? raw.workflow_id : crypto.randomUUID(),
    name: typeof raw.name === 'string' ? raw.name : 'Imported Workflow',
    version: typeof raw.version === 'string' ? raw.version : '1.0.0',
    description: typeof raw.description === 'string' ? raw.description : '',
    entry_node_id: typeof raw.entry_node_id === 'string' ? raw.entry_node_id : '',
    nodes,
    edges: [],
    metadata: isObject(raw.metadata) ? raw.metadata : {},
  };

  const ids = new Set(nodes.map((n) => n.node_id));
  for (const e of edges) {
    if (!ids.has(e.source_node_id) || !ids.has(e.target_node_id)) {
      notices.push(`Edge ${e.source_node_id} → ${e.target_node_id} points to a missing node and was not imported.`);
      continue;
    }
    const src = wf.nodes.find((n) => n.node_id === e.source_node_id)!;
    if (!src.allowed_peers.includes(e.target_node_id)) {
      wf = addPeer(wf, e.source_node_id, e.target_node_id);
      notices.push(`Edge ${e.source_node_id} → ${e.target_node_id} had no matching allowed_peers entry; "${e.target_node_id}" was added to ${e.source_node_id}.allowed_peers.`);
    }
  }
  return { ok: true, workflow: wf, notices };
}

/** The 3-agent workflow the backend runs by default (backend/app/services/run_service.py). */
export function defaultWorkflow(): WorkflowConfig {
  const mk = (node_id: string, name: string, role: AgentRole, peers: string[], tools: string[], x: number, y: number) =>
    setPosition(
      { node_id, name, role, model: 'mock', instructions: '', allowed_peers: peers, allowed_tools: tools, timeout_seconds: 30, call_limit: 10, metadata: {} },
      { x, y },
    );
  return {
    workflow_id: 'default_se_workflow',
    name: 'Software Engineering 3-Agent Workflow',
    version: '1.0.0',
    description: '',
    entry_node_id: 'backend_agent',
    nodes: [
      mk('backend_agent', 'Backend Agent', 'backend', ['db_manager_agent'], ['customer_db'], 0, 0),
      mk('db_manager_agent', 'DB Manager Agent', 'db_manager', ['qa_agent'], ['customer_db', 'workflow_memory'], 640, 0),
      mk('qa_agent', 'QA Agent', 'qa', [], ['test_suite'], 640, 320),
    ],
    edges: [],
    metadata: {},
  };
}
