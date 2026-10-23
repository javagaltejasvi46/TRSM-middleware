# TRSM Development Workplan — Debarshi

**Role:** Frontend engineering and visual playground  
**Primary ownership:** The visual workflow editor, node configuration, live execution view, audit-trace explorer, and metrics dashboard.

## 1. Project context

We are building an n8n-like playground for configuring a LangGraph-based multi-agent workflow. Users will drag in agents such as Backend, DB Manager, QA and DevOps, configure their roles/models/tools/permissions, connect allowed peers, and execute a run.

The defining visual feature is that **every agent node displays a TRSM Node Guard**, while a visible central **TRSM Agent Communication Gateway** mediates messages between agents. A separate resource gateway protects tool, database and memory access. Audit events feed trace and evaluation views.

The frontend visualizes configuration and backend decisions; it does not enforce policy itself. A user cannot bypass TRSM by editing browser state or changing a visual edge.

## 2. Screens and owned modules

### A. Workflow canvas

Use React + TypeScript + Vite and a node-editor library such as React Flow (`@xyflow/react`).

Required capabilities:
- Drag and drop supported node types onto a canvas.
- Connect nodes with edges that represent configured workflow/peer relationships.
- Show a TRSM Node Guard badge on every agent node.
- Show a central TRSM Communication Gateway and visually distinguish configured paths from policy-approved runtime messages.
- Save/load a workflow configuration.
- Validate basic graph structure before requesting execution.
- Provide clear invalid-state feedback rather than silently dropping nodes or edges.

The canvas edge means a route is configured, **not** that all messages on that edge will be approved. The runtime gateway remains authoritative.

### B. Node configuration panel

For each node, expose only fields supported by the backend contract:
- Node ID and display name.
- Agent role and task/instructions.
- Model/provider setting (for example, an Ollama model identifier).
- Allowed peer agents.
- Allowed tools/resources.
- Input/output configuration where supported.
- Timeout, call limits and risk threshold where supported.

Show policy and connection settings clearly. Do not store API secrets in the workflow JSON or browser local storage.

### C. Run and monitor view

- Start a workflow using the backend API.
- Display run status and current node.
- Show node states such as pending, running, succeeded, blocked, quarantined, failed and awaiting review.
- Display gateway decisions: ALLOW/BLOCK/QUARANTINE/REVIEW and the reason code returned by the backend.
- Show timestamps and per-node duration.
- Offer a clear path from an agent node to the relevant trace events.

Use polling first if live streaming is not yet available; do not build a complex websocket/SSE architecture before the backend needs it.

### D. Audit trace and evaluation dashboard

- Render events ordered by timestamp and linked by `run_id`, `trace_id`, `event_id` and `parent_event_id`.
- Filter by agent, event type, decision, threat type and run.
- Display provenance/source labels and blocked/quarantined outcomes.
- Show metrics returned by the backend: CSS, TUE, ASR, FPR/FNR, task success, latency and cost.
- Provide a baseline-vs-protected comparison view once the evaluation API is available.
- Label unavailable metrics as “not available” instead of making up placeholder results that look real.

## 3. Suggested frontend structure

```text
frontend/src/
  app/
  pages/
    PlaygroundPage.tsx
    RunDetailsPage.tsx
    EvaluationPage.tsx
  components/
    WorkflowCanvas/
    AgentNode/
    TrsmNodeGuardBadge/
    GatewayNode/
    NodeConfigPanel/
    RunControls/
    ExecutionTimeline/
    TraceExplorer/
    MetricsPanel/
  api/
    workflows.ts
    runs.ts
    events.ts
    metrics.ts
  types/
```

Adjust to the repository rather than creating a second competing structure. Keep canvas components separate from API access and trace rendering.

## 4. API and data contracts

Yashwanth owns backend routes and shared contract definitions. Agree the first API shape before wiring the UI. The likely API capabilities are:

- Create/update/read a workflow.
- Validate a workflow graph.
- Start a run and retrieve its status.
- Read run events/traces.
- Read per-run and comparison metrics.
- Request human review/resolve a review state, if included in the MVP.

Use the backend's OpenAPI schema or a shared agreed TypeScript contract. Do not invent response fields independently. At minimum, coordinate these objects:

`WorkflowConfig`, `AgentNodeConfig`, `WorkflowEdge`, `RunSummary`, `AuditEvent`, `PolicyDecision`, `ThreatFinding`, `MetricResult`.

An audit event should be able to show `event_id`, `run_id`, `trace_id`, optional `parent_event_id`, timestamp, actor/target, event type, decision/reason, and a safe payload summary or reference.

## 5. Milestones and acceptance criteria

### Milestone 1 — Static playground
- Canvas supports adding, moving, connecting and deleting supported nodes.
- Every agent node visibly has a TRSM Node Guard badge.
- Node configuration form validates required fields.
- Workflow graph can be exported/imported as JSON without losing node IDs or configured peer relationships.

### Milestone 2 — Backend integration
- Workflow validation and run start use real API responses.
- Backend errors and policy rejections are represented accurately.
- UI does not simulate a successful run when the backend did not report success.
- Agent-to-agent messages display the backend's policy decisions.

### Milestone 3 — Trace viewer
- A selected run's events can be browsed and filtered.
- Clicking an event reveals the relevant sender/receiver, reason code, provenance and parent/trace links when provided.
- Blocked and quarantined events are visibly distinct from delivered messages.

### Milestone 4 — Evaluation view
- Display real CSS/TUE/security/performance metrics from the API.
- Show baseline and protected values with run IDs and scenario context.
- Clearly indicate metric definitions and unavailable values; no fabricated results.

## 6. Shared engineering rules

- The frontend is an untrusted client. It can request configuration and execution, but backend gateways must enforce all permissions.
- A displayed connection does not grant permission unless the backend policy confirms it.
- Never call agents or tools directly from the browser.
- Do not render secrets, unrestricted tool output or sensitive payloads in the trace viewer.
- Use a consistent state model and accessible labels; avoid making color the only indication of ALLOW/BLOCK/QUARANTINE.
- Add component tests for node configuration, decision rendering and event filtering.

## 7. Agentic development workflow

Claude Code can accelerate scaffold creation and repetitive UI work, but generated UI code still needs integration checks:
1. Ask it to read the architecture and contract types before creating components.
2. Work in small vertical slices (canvas first, API integration next, traces after that).
3. Ask for a plan before changes and require it to list files modified.
4. Do not allow it to redefine backend API contracts or create mock security decisions as if they were authoritative.
5. Review node-graph serialization, React state updates, loading/error states and security-sensitive UI assumptions.
6. Run lint, typecheck, unit tests and a complete manual walkthrough after each slice.
7. Avoid accepting large unrelated refactors just because the page looks correct.

Useful Claude Code task prompt:

> Read the TRSM architecture and the agreed API/types first. Implement only `[specific UI slice]` using the existing stack. Preserve contracts, do not mock a successful security decision, include loading/error/empty states, add relevant tests, and report exactly which checks were executed.

## 8. Handoff to the research-paper team

Provide screenshots and stable descriptions of:
- the workflow graph and per-agent TRSM Node Guard;
- communication gateway decisions;
- a trace showing propagation/provenance and a blocked or quarantined message;
- actual evaluation results and baseline-versus-protected view.

Your success criterion is a usable, honest visualization of the runtime—not merely an attractive canvas. The UI must make it easy to understand why an agent message or action was allowed, blocked or reviewed.
