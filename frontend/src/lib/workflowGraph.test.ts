import { describe, expect, it } from 'vitest';
import {
  addNode,
  addPeer,
  createAgentNode,
  defaultWorkflow,
  deleteNode,
  deriveEdges,
  executionSignature,
  exportWorkflowJson,
  findFreePosition,
  getPosition,
  importWorkflowJson,
  moveNode,
  removePeer,
  updateNode,
} from './workflowGraph';

const edgePairs = (wf: Parameters<typeof deriveEdges>[0]) => deriveEdges(wf).map((e) => `${e.source_node_id}->${e.target_node_id}`);

describe('edge <-> allowed_peers sync', () => {
  it('derives edges from allowed_peers', () => {
    expect(edgePairs(defaultWorkflow())).toEqual(['backend_agent->db_manager_agent', 'db_manager_agent->qa_agent']);
  });

  it('adding and removing a peer adds and removes the edge', () => {
    let wf = addPeer(defaultWorkflow(), 'qa_agent', 'backend_agent');
    expect(edgePairs(wf)).toContain('qa_agent->backend_agent');
    expect(wf.nodes.find((n) => n.node_id === 'qa_agent')!.allowed_peers).toEqual(['backend_agent']);
    wf = removePeer(wf, 'qa_agent', 'backend_agent');
    expect(edgePairs(wf)).not.toContain('qa_agent->backend_agent');
  });

  it('ignores self-routes and duplicate peers', () => {
    let wf = addPeer(defaultWorkflow(), 'qa_agent', 'qa_agent');
    wf = addPeer(wf, 'backend_agent', 'db_manager_agent');
    expect(wf.nodes.find((n) => n.node_id === 'qa_agent')!.allowed_peers).toEqual([]);
    expect(wf.nodes.find((n) => n.node_id === 'backend_agent')!.allowed_peers).toEqual(['db_manager_agent']);
  });

  it('draws no edge for a peer that is not in the workflow', () => {
    const wf = addPeer(defaultWorkflow(), 'qa_agent', 'ghost_agent');
    expect(edgePairs(wf)).not.toContain('qa_agent->ghost_agent');
  });
});

describe('node operations', () => {
  it('creates unique node IDs and makes the first node the entry', () => {
    const empty = { ...defaultWorkflow(), nodes: [], entry_node_id: '' };
    const a = createAgentNode('qa', [], { x: 1, y: 2 });
    const wf = addNode(empty, a);
    const b = createAgentNode('qa', wf.nodes.map((n) => n.node_id), { x: 0, y: 0 });
    expect(a.node_id).toBe('qa_agent');
    expect(b.node_id).toBe('qa_agent_2');
    expect(wf.entry_node_id).toBe('qa_agent');
    expect(getPosition(a)).toEqual({ x: 1, y: 2 });
  });

  it('renaming a node updates peers that point to it and the entry node', () => {
    const wf = defaultWorkflow();
    const backend = wf.nodes.find((n) => n.node_id === 'backend_agent')!;
    const db = wf.nodes.find((n) => n.node_id === 'db_manager_agent')!;
    let next = updateNode(wf, 'db_manager_agent', { ...db, node_id: 'db' });
    expect(next.nodes.find((n) => n.node_id === 'backend_agent')!.allowed_peers).toEqual(['db']);
    expect(edgePairs(next)).toEqual(['backend_agent->db', 'db->qa_agent']);
    next = updateNode(next, 'backend_agent', { ...backend, node_id: 'api', allowed_peers: ['db'] });
    expect(next.entry_node_id).toBe('api');
  });

  it('deleting a node removes it from other peer lists and moves the entry', () => {
    const wf = deleteNode(defaultWorkflow(), 'backend_agent');
    expect(wf.nodes.map((n) => n.node_id)).toEqual(['db_manager_agent', 'qa_agent']);
    expect(wf.entry_node_id).toBe('db_manager_agent');
    const wf2 = deleteNode(defaultWorkflow(), 'qa_agent');
    expect(wf2.nodes.find((n) => n.node_id === 'db_manager_agent')!.allowed_peers).toEqual([]);
  });
});

describe('executionSignature', () => {
  it('ignores layout and the workflow name, but not agent config or routes', () => {
    const wf = defaultWorkflow();
    const sig = executionSignature(wf);
    expect(executionSignature(moveNode(wf, 'qa_agent', { x: 999, y: 999 }))).toBe(sig);
    expect(executionSignature({ ...wf, name: 'Renamed' })).toBe(sig);
    expect(executionSignature(addPeer(wf, 'qa_agent', 'backend_agent'))).not.toBe(sig);
    const qa = wf.nodes.find((n) => n.node_id === 'qa_agent')!;
    expect(executionSignature(updateNode(wf, 'qa_agent', { ...qa, allowed_tools: [] }))).not.toBe(sig);
  });
});

describe('findFreePosition', () => {
  const size = { width: 100, height: 50 };
  it('uses the centre when it is free', () => {
    expect(findFreePosition({ x: 0, y: 0 }, size, [])).toEqual({ x: -50, y: -25 });
  });
  it('moves off an occupied centre to a non-overlapping spot', () => {
    const occupied = [{ x: -150, y: -95, width: 300, height: 190 }];
    const p = findFreePosition({ x: 0, y: 0 }, size, occupied);
    const r = { ...p, ...size };
    const o = occupied[0];
    const overlap = r.x < o.x + o.width && r.x + r.width > o.x && r.y < o.y + o.height && r.y + r.height > o.y;
    expect(overlap).toBe(false);
  });
  it('stays inside the given bounds', () => {
    const occupied = [{ x: -150, y: -95, width: 300, height: 190 }];
    const bounds = { x: -400, y: -100, width: 800, height: 200 };
    const p = findFreePosition({ x: 0, y: 0 }, size, occupied, bounds);
    expect(p.y).toBeGreaterThanOrEqual(bounds.y);
    expect(p.y + size.height).toBeLessThanOrEqual(bounds.y + bounds.height);
    expect(p.x + size.width <= -150 - 24 || p.x >= 150 + 24).toBe(true);
  });
});

describe('JSON export / import', () => {
  it('round-trips without losing node IDs, peers, tools or positions', () => {
    const original = moveNode(defaultWorkflow(), 'qa_agent', { x: 123, y: -45 });
    const res = importWorkflowJson(exportWorkflowJson(original));
    expect(res.ok).toBe(true);
    if (!res.ok) return;
    expect(res.notices).toEqual([]);
    expect(res.workflow.nodes.map((n) => [n.node_id, n.allowed_peers, n.allowed_tools])).toEqual(
      original.nodes.map((n) => [n.node_id, n.allowed_peers, n.allowed_tools]),
    );
    expect(getPosition(res.workflow.nodes.find((n) => n.node_id === 'qa_agent')!)).toEqual({ x: 123, y: -45 });
    expect(res.workflow.entry_node_id).toBe('backend_agent');
    expect(res.workflow.workflow_id).toBe(original.workflow_id);
  });

  it('exports edges that match allowed_peers', () => {
    const json = JSON.parse(exportWorkflowJson(defaultWorkflow()));
    expect(json.edges).toEqual([
      { source_node_id: 'backend_agent', target_node_id: 'db_manager_agent', metadata: {} },
      { source_node_id: 'db_manager_agent', target_node_id: 'qa_agent', metadata: {} },
    ]);
  });

  it('rejects invalid JSON and malformed shapes instead of dropping data', () => {
    expect(importWorkflowJson('{not json').ok).toBe(false);
    expect(importWorkflowJson('[]').ok).toBe(false);
    expect(importWorkflowJson('{"nodes": "x"}').ok).toBe(false);
    const badNode = importWorkflowJson(JSON.stringify({ nodes: [{ node_id: 5, name: 'x' }] }));
    expect(badNode.ok).toBe(false);
    const badRole = importWorkflowJson(JSON.stringify({ nodes: [{ node_id: 'a', name: 'A', role: 'root' }] }));
    expect(badRole.ok).toBe(false);
    if (!badRole.ok) expect(badRole.errors.join(' ')).toMatch(/role "root"/);
    const badLimit = importWorkflowJson(JSON.stringify({ nodes: [{ node_id: 'a', name: 'A', call_limit: '10' }] }));
    expect(badLimit.ok).toBe(false);
  });

  it('reports peers added to match imported edges, and drops edges to missing nodes with a notice', () => {
    const res = importWorkflowJson(
      JSON.stringify({
        entry_node_id: 'a',
        nodes: [
          { node_id: 'a', name: 'A', allowed_peers: [] },
          { node_id: 'b', name: 'B' },
        ],
        edges: [
          { source_node_id: 'a', target_node_id: 'b' },
          { source_node_id: 'a', target_node_id: 'missing' },
        ],
      }),
    );
    expect(res.ok).toBe(true);
    if (!res.ok) return;
    expect(res.workflow.nodes[0].allowed_peers).toEqual(['b']);
    expect(res.notices).toHaveLength(2);
    expect(res.notices[0]).toMatch(/"b" was added to a\.allowed_peers/);
    expect(res.notices[1]).toMatch(/missing/);
  });
});
