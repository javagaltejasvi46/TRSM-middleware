# TRSM Development Workplan — Yashwanth

**Role:** Backend engineering and execution runtime  
**Primary ownership:** FastAPI backend, LangGraph orchestration, message/resource gateways, persistence, workflow execution APIs, and integration of the TRSM decision modules.

## 1. Project context

We are building a visual playground for running a small LangGraph-based multi-agent workflow. Users configure agents such as Backend, DB Manager, QA and DevOps from the frontend. Each agent displays a TRSM Node Guard, but enforcement must happen in the trusted backend.

**Non-negotiable architecture:** no agent-to-agent message can reach its recipient without passing through the central TRSM Agent Communication Gateway. Tool, database and memory operations must pass through a separately authorized resource gateway. Security and execution events are sent to a shared audit/event pipeline.

## 2. Your owned modules

### A. API and workflow configuration

Implement FastAPI endpoints and validated schemas for:
- Create, update, retrieve and validate workflow definitions.
- Start a workflow run and retrieve run status/results.
- Retrieve audit events/traces for a run.
- Retrieve CSS/TUE and security/performance results.
- Resolve a review state if human-in-the-loop review is included in the MVP.

Validate user-supplied workflow JSON on the server. Check node IDs, node types, declared edges, allowed peer definitions, required model/role fields and resource references. Never trust frontend graph validation as a security control.

### B. LangGraph runtime and agent lifecycle

- Compile a validated workflow definition into a LangGraph graph or controlled execution plan.
- Implement the supported agent nodes and a small initial demonstration workflow.
- Manage run state, node status, timeouts, failure handling and execution limits.
- Support an Ollama/local-model adapter when configured, while keeping a mock/deterministic adapter for tests and CI.
- Ensure agents produce message/action proposals with structured metadata; they do not directly pass arbitrary output into another agent's private state.

### C. Central Agent Communication Gateway

This is the most important backend boundary.

For every proposed inter-agent message:
1. Create/attach `run_id`, `trace_id`, `event_id` and source/parent references.
2. Authenticate/resolve the registered sender and intended receiver from the runtime context.
3. Submit the message and policy context to Tejasvi's decision engine/guardian interfaces.
4. Apply the decision returned by the trusted backend: `ALLOW`, `BLOCK`, `QUARANTINE`, or `REVIEW`.
5. Deliver only allowed messages to the target agent.
6. Retain blocked/quarantined messages outside the receiving agent's context; store only appropriately redacted evidence.
7. Emit structured events for the proposal, detector findings, policy decision and final delivery/block outcome.

Do not rely on prompts such as “agents must communicate safely.” Enforce this in code. Do not let agent outputs mutate trusted role/permission configuration.

### D. Resource Gateway for tools and memory

- Route every tool invocation through a single execution adapter/registry.
- Check role-scoped tool permissions, allowlists, argument schemas, rate limits and high-risk operations before execution.
- Route database and memory reads/writes through policy checks.
- Attach provenance to tool/memory results and return that metadata to the workflow.
- Provide sandboxed/mock tools for the demo; do not permit arbitrary shell or filesystem access by default.
- Keep communication permission separate from permission to execute a tool.

### E. Audit event collector and persistence

Start with SQLite for the local prototype unless the team has a justified reason to use PostgreSQL immediately. Define and own the initial shared Pydantic contract in coordination with Tejasvi and Debarshi.

Suggested core event fields:

```text
event_id, run_id, trace_id, parent_event_id, timestamp,
event_type, actor_id, target_id, source_type, trust_labels,
policy_decision, reason_code, policy_version,
duration_ms, safe_payload_summary, payload_reference
```

Not every field must be populated on every event. Preserve causal links so we can trace an untrusted instruction through multiple agents, a memory write, and a subsequent tool attempt. Redact secrets and avoid storing full raw prompts/results unless the experiment explicitly requires them and retention is controlled.

Record node start/completion, proposed/delivered agent messages, gateway decisions, tool calls/results, memory reads/writes, threat findings, and run completion/failure. Build query APIs so the frontend can filter events by run, actor, type and decision.

## 3. Suggested backend structure

```text
backend/
  app/
    main.py
    api/
      workflows.py
      runs.py
      events.py
      metrics.py
    contracts/
      workflow.py
      messages.py
      events.py
      decisions.py
    runtime/
      graph_compiler.py
      orchestrator.py
      agent_runner.py
      communication_gateway.py
      resource_gateway.py
      tool_registry.py
    trsm/
      interfaces.py   # agreed calls into Tejasvi's modules
    persistence/
      database.py
      event_repository.py
      workflow_repository.py
    tests/
```

This is a starting suggestion, not a demand to duplicate an existing repo structure. Keep the runtime, TRSM decision logic, API and persistence boundaries clear.

## 4. Integration contract with Tejasvi and Debarshi

### With Tejasvi

Agree interfaces before integrating:

```python
evaluate_agent_message(message, context) -> PolicyDecision
evaluate_resource_action(action, context) -> PolicyDecision
track_provenance(content, source_event) -> ProvenanceRecord
detect_threat(event, recent_trace) -> list[ThreatFinding]
calculate_css(run_trace) -> MetricResult
calculate_tue(run_trace) -> MetricResult
```

You own routing, execution, request/response contracts, and event persistence. Tejasvi owns the policy/detection/provenance/metric decision logic. Use stable typed contracts; do not reimplement the same logic in the gateway.

### With Debarshi

Publish the API contract through FastAPI/OpenAPI early. Agree endpoints and response models for workflows, runs, events and metrics. Debarshi's frontend must use returned policy decisions and trace events rather than fabricate them locally.

## 5. Milestones and acceptance criteria

### Milestone 1 — End-to-end skeleton
- FastAPI starts and exposes health plus workflow/run endpoints.
- A validated workflow can execute a small 3-agent deterministic test graph.
- Run/node status and errors are persisted.

### Milestone 2 — Enforcement routing
- Every inter-agent message is routed through the communication gateway.
- Integration tests prove a blocked message never appears in the recipient's inputs.
- Direct peer access and undeclared tool execution paths are absent or blocked.
- Every tool and memory operation goes through the resource gateway.

### Milestone 3 — Audit instrumentation
- Events have stable run/trace IDs and usable parent references.
- The trace reconstructs message → decision → delivery/block → later action.
- Trace APIs support the fields/filters required by Debarshi's UI.
- Database failures and partial runs are handled predictably.

### Milestone 4 — Full integration and demo
- Plug in Tejasvi's policy/guardian/metrics modules through stable interfaces.
- Integrate the playground frontend and show real execution events.
- Run the same scenarios with TRSM on and off.
- Include timeouts, mock tools, test fixtures and one-command local setup instructions.

## 6. Shared engineering rules

- The frontend is not a trust boundary; revalidate all workflow configuration on the backend.
- A displayed graph edge is not sufficient authorization; check the current policy on every message.
- Keep the orchestrator as the trusted owner of agent identity and workflow state.
- Make default tools safe and restricted. Do not expose arbitrary shell/file APIs for convenience.
- Use structured event records, not log-text parsing, for metrics and audits.
- Keep policy versions with decisions so experiments can be reproduced.
- Add integration tests at the enforcement boundary, not only unit tests for individual functions.

## 7. Agentic development workflow

Use coding agents for scaffolding, endpoint boilerplate, tests and refactors, but retain ownership of the trust boundary:
1. Create the module contract and a failing test before asking an agent to implement a gateway.
2. Restrict each agentic task to a small file/module set.
3. Ask the coding agent to identify potential bypass paths and write tests for them.
4. Review any generated code that handles agent identity, authorization, filesystem/shell tools, or message delivery.
5. Run unit and integration tests after every gateway change.
6. Keep changes on feature branches and merge only after Tejasvi/Debarshi contracts still pass.
7. Report only tests actually executed; keep a reproducible local setup.

Useful task prompt:

> Read the current workflow, event and decision contracts. Implement only `[backend module]`. Preserve the gateway as the mandatory path for all inter-agent messages and resource operations. Add tests proving unauthorized or malformed requests cannot bypass enforcement. Do not change public contracts without proposing the change first, and list tests actually run.

## 8. Handoff to the research-paper team

Provide versioned workflow definitions, run IDs, structured traces, policy versions, tool/mock configuration and repeatable baseline/protected execution commands. The researchers need enough data to independently reproduce metric tables and verify that blocked attacks were actually prevented without breaking benign tasks.

Your success criterion is an execution backend where every communication and resource action has an enforceable path, a traceable decision, and evidence suitable for evaluation.
