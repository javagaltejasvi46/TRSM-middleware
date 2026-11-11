import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MarkerType,
  applyNodeChanges,
  applyEdgeChanges,
  useReactFlow,
  type Connection,
  type Edge,
  type EdgeChange,
  type NodeChange,
  type NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { AgentNode, type AgentFlowNode } from '../AgentNode/AgentNode';
import { GatewayNode, type GatewayFlowNode } from '../CommunicationGateway/GatewayNode';
import { NodePalette, ROLE_DRAG_TYPE } from '../NodePalette/NodePalette';
import { AgentRole, AgentStatus, WorkflowConfig } from '../../types';
import { AGENT_ROLES, deriveEdges, findFreePosition, getPosition, type Rect, type XYPosition } from '../../lib/workflowGraph';

const NEW_NODE_SIZE = { width: 260, height: 180 };

type FlowNode = AgentFlowNode | GatewayFlowNode;

export const GATEWAY_NODE_ID = '__trsm_gateway__';

const nodeTypes: NodeTypes = { agent: AgentNode, gateway: GatewayNode };

export interface WorkflowCanvasProps {
  workflow: WorkflowConfig;
  selectedNodeId: string | null;
  nodeStatuses?: Record<string, AgentStatus>;
  gatewayStats: { mediated: number | null; blocked: number | null };
  onSelectNode: (nodeId: string | null) => void;
  onAddNode: (role: AgentRole, position: XYPosition) => void;
  onMoveNode: (nodeId: string, position: XYPosition) => void;
  onDeleteNodes: (nodeIds: string[]) => void;
  onAddPeer: (sourceId: string, targetId: string) => void;
  onRemovePeer: (sourceId: string, targetId: string) => void;
}

const edgeId = (s: string, t: string) => `route:${s}->${t}`;

function CanvasInner(props: WorkflowCanvasProps) {
  const { workflow, selectedNodeId, nodeStatuses, gatewayStats } = props;
  const { screenToFlowPosition } = useReactFlow();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [nodes, setNodes] = useState<FlowNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  // Rebuild React Flow nodes from the workflow, keeping measured sizes and the
  // gateway's position (the gateway is not part of WorkflowConfig).
  useEffect(() => {
    setNodes((prev) => {
      const prevById = new Map(prev.map((n) => [n.id, n]));
      const gwPrev = prevById.get(GATEWAY_NODE_ID);
      const gateway: GatewayFlowNode = {
        id: GATEWAY_NODE_ID,
        type: 'gateway',
        position: gwPrev?.position ?? { x: 300, y: 200 },
        measured: gwPrev?.measured,
        data: { ...gatewayStats },
        deletable: false,
        connectable: false,
        selectable: false,
        // Behind the routes, so routes crossing the centre stay visible and clickable.
        zIndex: -1,
      };
      const routes = deriveEdges(workflow);
      const withOut = new Set(routes.map((r) => r.source_node_id));
      const withIn = new Set(routes.map((r) => r.target_node_id));
      const agents: AgentFlowNode[] = workflow.nodes.map((n) => ({
        id: n.node_id,
        type: 'agent',
        position: getPosition(n),
        measured: prevById.get(n.node_id)?.measured,
        selected: n.node_id === selectedNodeId,
        data: {
          config: n,
          isEntry: n.node_id === workflow.entry_node_id,
          status: nodeStatuses?.[n.node_id] ?? 'idle',
          hasIncoming: withIn.has(n.node_id),
          hasOutgoing: withOut.has(n.node_id),
        },
      }));
      return [gateway, ...agents];
    });
  }, [workflow, selectedNodeId, nodeStatuses, gatewayStats]);

  useEffect(() => {
    setEdges(
      deriveEdges(workflow).map((e) => ({
        id: edgeId(e.source_node_id, e.target_node_id),
        source: e.source_node_id,
        target: e.target_node_id,
        label: 'configured route',
        labelStyle: { fill: '#3730a3', fontSize: 11, fontWeight: 600 },
        labelBgStyle: { fill: '#ffffff', stroke: '#c7d2fe' },
        labelBgPadding: [6, 3] as [number, number],
        labelBgBorderRadius: 6,
        style: { stroke: '#6366f1', strokeWidth: 2, strokeDasharray: '6 4' },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1' },
        ariaLabel: `Configured route from ${e.source_node_id} to ${e.target_node_id}`,
      })),
    );
  }, [workflow]);

  const onNodesChange = useCallback(
    (changes: NodeChange<FlowNode>[]) => {
      setNodes((nds) => applyNodeChanges(changes, nds));
      for (const c of changes) {
        if (c.type === 'select' && c.id !== GATEWAY_NODE_ID) {
          if (c.selected) props.onSelectNode(c.id);
          else if (c.id === selectedNodeId) props.onSelectNode(null);
        }
      }
    },
    [props, selectedNodeId],
  );

  // Positions update locally while dragging; commit to the workflow on drop.
  const onNodeDragStop = useCallback(
    (_: unknown, node: FlowNode) => {
      if (node.id !== GATEWAY_NODE_ID) props.onMoveNode(node.id, node.position);
    },
    [props],
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      setEdges((eds) => applyEdgeChanges(changes, eds));
    },
    [],
  );

  const onEdgesDelete = useCallback(
    (deleted: Edge[]) => deleted.forEach((e) => props.onRemovePeer(e.source, e.target)),
    [props],
  );

  const onNodesDelete = useCallback(
    (deleted: FlowNode[]) => props.onDeleteNodes(deleted.filter((n) => n.id !== GATEWAY_NODE_ID).map((n) => n.id)),
    [props],
  );

  const onConnect = useCallback(
    (c: Connection) => {
      if (c.source && c.target && c.source !== GATEWAY_NODE_ID && c.target !== GATEWAY_NODE_ID) props.onAddPeer(c.source, c.target);
    },
    [props],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const role = e.dataTransfer.getData(ROLE_DRAG_TYPE) as AgentRole;
      if (!AGENT_ROLES.includes(role)) return;
      props.onAddNode(role, screenToFlowPosition({ x: e.clientX, y: e.clientY }));
    },
    [props, screenToFlowPosition],
  );

  // Click-to-add: place the node in the free spot nearest the centre of the view.
  const addAtCenter = useCallback(
    (role: AgentRole) => {
      const rect = wrapperRef.current?.getBoundingClientRect();
      if (!rect) return;
      const center = screenToFlowPosition({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 });
      const topLeft = screenToFlowPosition({ x: rect.left, y: rect.top });
      const bottomRight = screenToFlowPosition({ x: rect.right, y: rect.bottom });
      const visible: Rect = { ...topLeft, width: bottomRight.x - topLeft.x, height: bottomRight.y - topLeft.y };
      const occupied: Rect[] = nodes.map((n) => ({
        ...n.position,
        width: n.measured?.width ?? NEW_NODE_SIZE.width,
        height: n.measured?.height ?? NEW_NODE_SIZE.height,
      }));
      // Fall back to an unbounded search if the visible area has no free spot.
      const inView = findFreePosition(center, NEW_NODE_SIZE, occupied, visible);
      const fits = !occupied.some((o) => o.x < inView.x + NEW_NODE_SIZE.width && o.x + o.width > inView.x && o.y < inView.y + NEW_NODE_SIZE.height && o.y + o.height > inView.y);
      props.onAddNode(role, fits ? inView : findFreePosition(center, NEW_NODE_SIZE, occupied));
    },
    [props, screenToFlowPosition, nodes],
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%' }}>
      <NodePalette onAdd={addAtCenter} />
      <div
        ref={wrapperRef}
        style={{ flex: 1, minHeight: 0 }}
        onDragOver={(e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'move';
        }}
        onDrop={onDrop}
      >
      <ReactFlow<FlowNode, Edge>
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodesDelete={onNodesDelete}
        onEdgesDelete={onEdgesDelete}
        onNodeDragStop={onNodeDragStop}
        onConnect={onConnect}
        onPaneClick={() => props.onSelectNode(null)}
        // Selecting a route clears the node selection, so Delete removes only the route.
        onEdgeClick={() => props.onSelectNode(null)}
        // The gateway is not selectable; clicking it clears the selection like the pane does.
        onNodeClick={(_, n) => n.id === GATEWAY_NODE_ID && props.onSelectNode(null)}
        deleteKeyCode={['Delete', 'Backspace']}
        colorMode="light"
        style={{ background: "var(--canvas-bg)" }}
        fitView
        fitViewOptions={{ padding: 0.15 }}
      >
        <Background gap={20} size={1.5} color="#c7d2fe" />
        <Controls showInteractive={false} />
      </ReactFlow>
      </div>
    </div>
  );
}

export const WorkflowCanvas: React.FC<WorkflowCanvasProps> = (props) => (
  <ReactFlowProvider>
    <CanvasInner {...props} />
  </ReactFlowProvider>
);
