# TRSM Repository Structure and Development Conventions

**Status:** Proposed repository blueprint  
**Project:** TRSM Middleware for Trust, Risk, and Security Management in LLM-Based Agentic Multi-Agent Systems  
**Purpose:** This document defines the recommended monorepo layout, module boundaries, code ownership, shared contracts, test strategy, and rules for human and AI-assisted development.

> This is a proposed structure, not a statement that these files already exist. Inspect the repository before creating or moving files. Preserve working code where possible and update this document through a reviewed decision if the structure needs to change.

---

## 1. The design choice

Use a **single monorepo** with a React/TypeScript frontend and a Python/FastAPI backend. Keep one backend application at first; do not split the gateways, policy engine, audit collector, and metrics engine into separate microservices before measurements show a need.

The repository is organized around four implementation areas:

1. **Playground UI** — workflow canvas, agent configuration, live run view, audit explorer, and evaluation dashboard.
2. **Runtime and backend** — API, workflow validation, LangGraph orchestration, gateway routing, controlled resource access, persistence, and run lifecycle.
3. **TRSM logic and evaluation** — policy decisions, provenance, runtime threat findings, CSS/TUE calculation, and reproducible security evaluation.
4. **Documentation and experiments** — architecture contracts, test scenarios, evaluation protocols, results, and research artifacts.

### Non-negotiable system invariant

- Every inter-agent message must pass through the backend's **TRSM Agent Communication Gateway** before delivery.
- Every tool, database, and memory operation must pass through the **Controlled Resource Gateway** and receive its own authorization decision.
- The **Policy Enforcement Engine** is the authoritative source for `ALLOW`, `BLOCK`, `QUARANTINE`, or `REVIEW` decisions.
- A node badge, graph edge, model instruction, or frontend value is not a security boundary.

---

## 2. Recommended top-level structure

```text
trsm-project/
├── README.md
├── AGENTS.md
├── TRSM_MASTER_PROJECT_SPEC.md
├── STRUCTURE.md
├── .gitignore
├── .editorconfig
├── .env.example
├── Makefile                         # Optional convenience commands
│
├── docs/
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── agent-communication.md
│   │   ├── resource-enforcement.md
│   │   ├── audit-and-instrumentation.md
│   │   └── diagrams/                # Editable Mermaid sources or exported diagrams
│   ├── decisions/                   # Architecture Decision Records (ADRs)
│   │   ├── 0001-monorepo.md
│   │   ├── 0002-langgraph-runtime.md
│   │   └── 0003-contract-ownership.md
│   ├── design/
│   │   ├── system-design.md
│   │   ├── detailed-module-design.md
│   │   └── api-contracts.md
│   ├── research/
│   │   ├── literature-survey.md
│   │   ├── research-gap.md
│   │   └── references.md
│   ├── evaluation/
│   │   ├── experiment-protocol.md
│   │   ├── metric-definitions.md
│   │   └── threat-model.md
│   └── team/
│       ├── workplan-tejasvi.md
│       ├── workplan-debarshi.md
│       └── workplan-yashwanth.md
│
├── frontend/
│   ├── package.json
│   ├── package-lock.json             # Or pnpm-lock.yaml/yarn.lock; choose one only
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── .env.example
│   ├── public/
│   ├── src/
│   │   ├── app/                      # App shell, routes, global providers
│   │   ├── pages/
│   │   │   ├── PlaygroundPage.tsx
│   │   │   ├── RunDetailsPage.tsx
│   │   │   └── EvaluationPage.tsx
│   │   ├── components/
│   │   │   ├── WorkflowCanvas/
│   │   │   ├── AgentNode/
│   │   │   ├── TrsmNodeGuardBadge/
│   │   │   ├── CommunicationGateway/
│   │   │   ├── NodeConfigPanel/
│   │   │   ├── RunControls/
│   │   │   ├── ExecutionTimeline/
│   │   │   ├── TraceExplorer/
│   │   │   └── MetricsPanel/
│   │   ├── features/                 # Feature-level UI state and hooks if needed
│   │   ├── api/                      # HTTP calls; no direct agent/tool execution
│   │   │   ├── client.ts
│   │   │   ├── workflows.ts
│   │   │   ├── runs.ts
│   │   │   ├── events.ts
│   │   │   └── metrics.ts
│   │   ├── types/                    # Generated or derived API types; avoid hand drift
│   │   ├── utils/
│   │   └── styles/
│   └── tests/
│       ├── unit/
│       └── e2e/
│
├── backend/
│   ├── pyproject.toml                # Preferred Python dependency/tool configuration
│   ├── .env.example
│   ├── app/
│   │   ├── main.py                   # FastAPI app creation and router registration
│   │   ├── config.py                 # Validated settings; secrets loaded from environment
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── routes/
│   │   │       ├── health.py
│   │   │       ├── workflows.py
│   │   │       ├── runs.py
│   │   │       ├── events.py
│   │   │       ├── metrics.py
│   │   │       └── reviews.py         # Only if REVIEW/HITL is enabled in MVP
│   │   ├── schemas/                   # Canonical Pydantic contracts
│   │   │   ├── workflow.py
│   │   │   ├── agent.py
│   │   │   ├── messages.py
│   │   │   ├── policy.py
│   │   │   ├── resources.py
│   │   │   ├── provenance.py
│   │   │   ├── events.py
│   │   │   ├── threats.py
│   │   │   └── metrics.py
│   │   ├── services/                  # Application use cases; coordinates modules
│   │   │   ├── workflow_service.py
│   │   │   ├── run_service.py
│   │   │   ├── trace_service.py
│   │   │   └── evaluation_service.py
│   │   ├── runtime/                   # Yashwanth: runtime integration and routing
│   │   │   ├── orchestrator.py
│   │   │   ├── graph_validator.py
│   │   │   ├── graph_compiler.py
│   │   │   ├── agent_runner.py
│   │   │   ├── node_guard.py
│   │   │   ├── communication_gateway.py
│   │   │   ├── resource_gateway.py
│   │   │   ├── tool_registry.py
│   │   │   └── adapters/
│   │   │       └── ollama_adapter.py
│   │   ├── trsm/                      # Tejasvi: security/measurement logic
│   │   │   ├── policy_engine.py
│   │   │   ├── policy_rules.py
│   │   │   ├── provenance.py
│   │   │   ├── label_tracker.py
│   │   │   ├── runtime_guardian.py
│   │   │   ├── detectors/
│   │   │   │   ├── prompt_injection.py
│   │   │   │   ├── memory_poisoning.py
│   │   │   │   └── role_hijacking.py
│   │   │   └── decision_evidence.py
│   │   ├── audit/                     # Shared audit/instrumentation pipeline
│   │   │   ├── event_collector.py
│   │   │   ├── event_factory.py
│   │   │   ├── trace_builder.py
│   │   │   ├── redaction.py
│   │   │   └── integrity.py           # Hash chaining only if enabled/tested
│   │   ├── persistence/
│   │   │   ├── db.py
│   │   │   ├── models.py
│   │   │   ├── repositories/
│   │   │   │   ├── workflow_repository.py
│   │   │   │   ├── run_repository.py
│   │   │   │   ├── event_repository.py
│   │   │   │   └── policy_repository.py
│   │   │   └── migrations/
│   │   ├── evaluation/                # Tejasvi: metrics and repeatable experiment runner
│   │   │   ├── metrics/
│   │   │   │   ├── css.py
│   │   │   │   ├── tue.py
│   │   │   │   ├── security.py
│   │   │   │   └── performance.py
│   │   │   ├── runner.py
│   │   │   ├── baseline.py
│   │   │   ├── protected.py
│   │   │   └── report.py
│   │   └── utilities/
│   └── tests/
│       ├── unit/
│       │   ├── trsm/
│       │   ├── audit/
│       │   └── evaluation/
│       ├── integration/
│       │   ├── test_message_gateway.py
│       │   ├── test_resource_gateway.py
│       │   ├── test_provenance_flow.py
│       │   └── test_audit_pipeline.py
│       ├── api/
│       └── fixtures/
│
├── scenarios/                        # Versioned, reproducible test inputs
│   ├── benign/
│   ├── prompt_injection/
│   ├── memory_poisoning/
│   ├── role_hijacking/
│   └── resource_authorization/
│
├── scripts/
│   ├── dev.sh
│   ├── test.sh
│   ├── run_demo.py
│   ├── run_evaluation.py
│   └── export_api_types.sh
│
├── artifacts/                        # Generated output; not general source code
│   ├── examples/                      # Small non-sensitive sample traces/reports
│   └── .gitkeep
│
└── .github/
    └── workflows/
        └── ci.yml
```

This is a target layout. The first MVP can omit empty directories, the human-review endpoint, hash-chain integrity, database migrations, E2E browser tests, or CI automation until their prerequisites exist. Do not create abstractions merely to match the diagram.

---

## 3. Module responsibilities and boundaries

### 3.1 Frontend — Debarshi

Owns `frontend/`.

- Build a React + TypeScript workflow canvas; use React Flow (`@xyflow/react`) unless a concrete issue justifies another editor.
- Every agent node visually displays a TRSM Node Guard and current runtime status.
- Show the central communication gateway and make configured graph edges visually distinct from messages approved during a run.
- Configure agent ID, role, instructions, model, allowed peers, tools/resources, timeouts and limits where supported by the backend schema.
- Display real run states, decisions, reason codes, trace events and returned metrics.
- Use API calls only. The browser must never call an LLM, tool, database, or peer agent directly.
- Do not create fabricated security results to make the UI look complete. Label unavailable data clearly.

### 3.2 Backend runtime — Yashwanth

Owns `backend/app/api/`, `services/`, `runtime/`, and `persistence/`, plus application bootstrapping.

- Validate workflow configurations on the server; frontend validation is only a usability aid.
- Treat the orchestrator as the trusted source of sender identity and current graph/run state.
- Route every proposed message through `communication_gateway.py` and the policy engine before delivery.
- Route every tool, database and memory request through `resource_gateway.py` and authorize it independently.
- Integrate LangGraph and the chosen model adapter behind clear interfaces.
- Persist run/event state and provide endpoints for workflow configuration, execution, traces and metrics.
- Never add a direct agent-to-agent shortcut or let a node use an unrestricted resource client.

### 3.3 TRSM logic and evaluation — Tejasvi

Owns `backend/app/trsm/` and `backend/app/evaluation/`.

- Implement deterministic policy decisions, reason codes, peer/role/resource rules, and fail-closed cases.
- Track provenance and labels through message hops and memory read/write operations.
- Implement findings for prompt-injection propagation, memory poisoning and role/orchestrator hijacking.
- Keep detection separate from authorization; a detector emits a finding but cannot grant a capability.
- Implement CSS/TUE after agreeing on the original paper definitions and the testbed data needed by them.
- Implement ASR, FPR/FNR, task-success, latency/cost calculations and repeatable baseline/protected trial execution.
- Provide unit tests and a written description of metric assumptions and denominators.

### 3.4 Shared modules

The `schemas/` package is canonical for backend wire contracts. The `audit/` package is shared infrastructure that all runtime/TRSM modules call to emit events. Changes to shared schemas require agreement from all three developers before merge.

Do not have both `runtime/` and `trsm/` implement separate policy logic. Runtime calls TRSM logic; it does not re-implement its rules.

---

## 4. Dependency direction

Keep dependencies flowing inward toward schemas and domain logic; avoid circular imports.

```text
API routes
   ↓
Application services
   ↓
Runtime orchestration / gateways ───────→ TRSM decision logic
   ↓                                      ↓
Persistence / resource adapters          Findings and decisions
   └──────────────────┬───────────────────┘
                      ↓
              Audit event interfaces
                      ↓
             Trace store / metrics API
                      ↓
              Frontend presentation
```

Practical rules:

1. `schemas/` should hold typed data contracts, not call databases, LLMs, or HTTP endpoints.
2. `trsm/` should receive data and return typed decisions/findings. It should not invoke tools or directly deliver messages.
3. `runtime/communication_gateway.py` is the trusted routing point. It calls the policy engine and delivers only after an `ALLOW` decision.
4. `runtime/resource_gateway.py` is the trusted point for tool/database/memory operations and makes a separate policy check.
5. `audit/` stores structured, redacted events. It should not decide whether a request is authorized.
6. `evaluation/` consumes run traces and scenario outcomes; it must not infer results from free-form log text.
7. `api/` exposes application capabilities but should not contain policy rules or graph-execution logic directly.
8. `frontend/` is a client of the API and must never be treated as an authority for security decisions.

---

## 5. Canonical contracts

Before parallel implementation, agree these models in `backend/app/schemas/`. Use Pydantic types and enums; do not pass unstructured dictionaries across module boundaries except at explicitly external integration edges.

### 5.1 Required logical models

- `WorkflowConfig` — workflow ID, version, node configurations, configured edges and workflow settings.
- `AgentNodeConfig` — node ID, role, model reference, instructions, allowed peers, tool/resource permissions, timeouts and call limits.
- `AgentMessageProposal` — run/trace identifiers, sender/recipient, content or safe payload reference, source event references and metadata.
- `ResourceActionRequest` — agent identity, resource/tool name, operation, validated arguments, risk context and provenance references.
- `PolicyDecision` — decision enum, reason code, policy version, evidence references, applicable rule IDs and optional review requirement.
- `ProvenanceRecord` — origin type, source event IDs, trust/integrity label and lineage references.
- `ThreatFinding` — threat family, severity, confidence if applicable, evidence, source event and recommended action.
- `AuditEvent` — event/run/trace IDs, parent event if known, timestamp, actor/target, event type, decision/reason, policy version, timing and redacted summary/reference.
- `RunSummary` — status, timestamps, workflow version, task outcome, failure details and metrics references.
- `MetricResult` — metric name/version, value, numerator/denominator or component measurements, run/scenario references and limitations.

### 5.2 Decision values

Use one enum everywhere:

```text
ALLOW
BLOCK
QUARANTINE
REVIEW
```

Do not use alternate strings such as `DENY`, `PASS`, or `APPROVED` in some components without an explicit mapping at an external boundary. An operation can only be delivered/executed after the authoritative policy result is `ALLOW`. `REVIEW` requires a defined paused/approval flow; until that is implemented, it must not silently fall through to allow.

### 5.3 Message and event identity

Every request/run should include stable IDs where applicable:

- `run_id` — one workflow execution.
- `trace_id` — one trace/correlation scope.
- `event_id` — one immutable event record.
- `parent_event_id` — causal parent when known.
- `sender_id` / `recipient_id` — identities derived from trusted runtime state.
- `policy_version` — policy revision that produced the decision.

Do not trust a model-generated sender field as proof of identity. The orchestrator must bind the actual executing node identity to the proposal.

### 5.4 Frontend type sync

The backend owns canonical Pydantic contracts. Prefer generating TypeScript API types from FastAPI's OpenAPI document through `scripts/export_api_types.sh`. If generation is temporarily unavailable, manually synchronize frontend types and require a contract review; do not maintain a second incompatible schema set.

---

## 6. Communication, resource access, and audit sequence

### 6.1 Inter-agent message

```text
Agent node proposes a message
          ↓
Node Guard adds trusted runtime metadata
          ↓
Central Communication Gateway
          ↓
Verify registered sender / recipient / current workflow edge
          ↓
Load applicable policy and provenance context
          ↓
Runtime Guardian emits optional findings
          ↓
Policy Enforcement Engine returns a decision
          ├── ALLOW       → deliver to receiver
          ├── BLOCK       → reject; receiver gets nothing
          ├── QUARANTINE  → hold content from receiver
          └── REVIEW      → pause for approval if implemented
          ↓
Record proposal, evidence, decision, and delivery/block outcome
```

The visible node guard is not a separate trusted security service for every agent. It is the per-node integration/status surface; enforcement occurs in backend-controlled routing and policy code.

### 6.2 Tool/database/memory action

```text
Agent proposes a resource action
          ↓
Controlled Resource Gateway
          ↓
Validate resource + operation + arguments + agent permission
          ↓
Policy Engine + relevant provenance/risk checks
          ├── non-ALLOW → no resource operation executes
          └── ALLOW     → invoke registered adapter only
                              ↓
                         capture result
                              ↓
                   attach result provenance and audit event
```

A message allowed to reach an agent does not automatically authorize that agent's proposed tool action. Every resource operation is evaluated independently.

### 6.3 Audit event creation

Events should be emitted by the code path that knows what actually happened. Log proposal and decision separately from delivery/execution outcome. A `BLOCK` decision is not proof the attack succeeded; an alert is not proof an attack was stopped. Evaluation needs the actual scenario objective and final outcome.

---

## 7. Audit and evaluation layout

### 7.1 Audit events

Use structured event objects, not plain text strings. Initial event types may include:

```text
workflow.started
workflow.completed
workflow.failed
agent.started
agent.completed
message.proposed
message.policy_decided
message.delivered
message.blocked
message.quarantined
resource.proposed
resource.policy_decided
resource.executed
resource.blocked
memory.read
memory.write
threat.detected
review.requested
review.resolved
evaluation.completed
```

Only add event types that correspond to actual code paths. Keep `event_type` values documented and versioned.

### 7.2 Metrics and evidence

Metrics should be organized under `backend/app/evaluation/metrics/`; raw scenario definitions live under `scenarios/`; output from runs lives under `artifacts/` or another explicitly configured output directory.

- CSS: use the selected literature definition and document inputs/normalization/aggregation.
- TUE: use the selected literature definition and document its component measurements.
- ASR: define an attack trial as successful only when its stated objective is achieved.
- FPR/FNR: document positive/negative ground-truth labels and denominators.
- Task success: track clean and adversarial tasks separately.
- Overhead: compare baseline and protected runs under matched conditions; report latency distribution, not only one average, and record token/tool cost when available.

Do not combine metrics into a single opaque score that hides security or utility regressions. Store per-trial results and produce reproducible aggregate reports.

### 7.3 Artifact policy

- Keep small, sanitized example traces and reports in version control when useful.
- Do not commit secrets, personal data, full unredacted prompts, large output dumps, databases, model files, virtual environments, or build outputs.
- Store benchmark outputs with a scenario version, config/policy version and code revision so they can be reproduced.

---

## 8. Scenario and test organization

Use versioned files under `scenarios/`, with a consistent schema once agreed. Each scenario should state its purpose, task objective, relevant agents/tools, setup, expected security outcome, and ground-truth label for evaluation.

```text
scenarios/
├── benign/
│   ├── backend_to_db_allowed.yaml
│   └── qa_read_test_result.yaml
├── prompt_injection/
│   ├── direct_instruction_override.yaml
│   └── propagated_external_instruction.yaml
├── memory_poisoning/
│   └── untrusted_memory_write.yaml
├── role_hijacking/
│   └── unauthorized_role_change.yaml
└── resource_authorization/
    ├── unknown_tool.yaml
    └── write_without_permission.yaml
```

### Minimum tests for each enforcement rule

- a valid allowed request;
- a forbidden request;
- malformed or incomplete input;
- an unknown agent/tool/resource;
- a benign request that resembles an attack;
- an attempted gateway bypass;
- an audit assertion for the outcome.

Prefer deterministic/mock tools for CI. Add live/local LLM tests as a separate optional suite because model responses and latency can vary.

---

## 9. Configuration and environment

- Backend settings belong in validated configuration (`backend/app/config.py`) populated from environment variables.
- Commit `.env.example` files with variable names and safe placeholders only; never commit actual keys, passwords, or tokens.
- Keep provider selection configurable. The first local LLM adapter may use Ollama, but unit and integration tests must work with deterministic fake agents and mock tools without requiring Ollama.
- Do not let workflow JSON hold credentials. Reference server-side credentials through named configuration identifiers if external services are added later.
- Configure default bind address, storage paths and CORS conservatively for local development; document any change needed for network access.

Suggested first local setup commands should be documented in `README.md`. If a one-command `Makefile`/shell script is added, ensure the equivalent manual backend/frontend commands are also documented for users who do not have the relevant shell tooling.

---

## 10. Development ownership and collaboration

| Person | Primary ownership | Files/modules |
|---|---|---|
| **Tejasvi** | TRSM decisions, provenance, runtime threat detection, metrics and evaluation | `backend/app/trsm/`, `backend/app/evaluation/`, their unit tests, evaluation protocol |
| **Yashwanth** | FastAPI, LangGraph orchestration, gateway routing, persistence and API integration | `backend/app/api/`, `services/`, `runtime/`, `persistence/`, integration/API tests |
| **Debarshi** | Visual playground, node editor, configuration UI, trace and metrics views | `frontend/`, frontend tests, UI documentation |
| **Research team (2 people)** | Paper, literature review, experimental protocol and results write-up | `docs/research/`, `docs/evaluation/`, report artifacts; coordinate metric definitions with Tejasvi |

Ownership means one person is responsible for the module; it does not mean they can change shared contracts unilaterally.

### Contract handshake before parallel work

Agree a first version of `WorkflowConfig`, `AgentMessageProposal`, `ResourceActionRequest`, `PolicyDecision`, `ThreatFinding`, `AuditEvent`, `RunSummary`, and `MetricResult`. Commit these before independent modules are deeply implemented.

Recommended order:

1. Yashwanth drafts the Pydantic schemas and minimum API surface.
2. Tejasvi reviews policy inputs/outputs and metric/event evidence needs.
3. Debarshi confirms the UI can render required config, states, trace filters and metrics.
4. Team agrees the schema changes; then frontend types are generated from OpenAPI.

---

## 11. Agentic development rules

AI coding agents (including Claude Code) are development assistants, not project authorities. They can scaffold components, generate tests, explain failures and implement bounded changes, but they must follow this file and the master project specification.

For each coding task:

1. Ask the agent to read `AGENTS.md`, `TRSM_MASTER_PROJECT_SPEC.md`, `STRUCTURE.md`, and the relevant contract before editing.
2. Give it one bounded task, explicit files/modules in scope, and acceptance criteria.
3. Ask it to inspect existing code first and propose a plan.
4. Prohibit unrelated refactors and silent public-schema changes.
5. Require tests for allow, deny, malformed, benign-lookalike and bypass cases where relevant.
6. Inspect the diff, especially authorization, identity, provenance, secret handling and metrics formulas.
7. Run appropriate lint/type checks/tests and review the actual outputs.
8. Commit small changes on a feature branch; do not let multiple agents edit the same shared contract concurrently.
9. Require the coding agent to report which commands were run and which checks remain unexecuted.

### Suggested root `AGENTS.md` principles

`AGENTS.md` should contain concise, durable rules: read the master spec; preserve mandatory message/resource mediation; never treat frontend state as security authority; use canonical Pydantic schemas; do not invent metric definitions/results; add tests; and report actual verification. Keep detailed architecture in this file and the master specification rather than duplicating hundreds of lines in `AGENTS.md`.

---

## 12. Branching, commits, and change control

- Use one branch per bounded feature or fix, such as `feat/message-gateway`, `feat/trace-viewer`, or `test/memory-poisoning-scenarios`.
- Keep commits small and explain the user-visible or security-relevant change.
- Require review for changes to `schemas/`, policy defaults, gateway routing, audit event definitions, metric calculations, and tool/resource permissions.
- Record substantial architecture changes as an ADR under `docs/decisions/`.
- Do not check in generated artifacts unless they are intended test fixtures or sanitized research evidence.
- Keep lockfiles under version control; use one package manager consistently per ecosystem.

---

## 13. Minimum root README contents

The repository `README.md` should not repeat the full specification. It should explain:

1. What TRSM is and what the prototype is intended to demonstrate.
2. One small architecture diagram.
3. Project status and known limitations.
4. Prerequisites (Python version, Node version, and optional Ollama).
5. Setup and run commands for backend/frontend.
6. How to run tests and the deterministic demo.
7. How to execute the baseline/protected evaluation.
8. Links to `TRSM_MASTER_PROJECT_SPEC.md`, `STRUCTURE.md`, and detailed design docs.
9. Security note: never use unrestricted or production credentials in demo workflows.

---

## 14. Suggested milestone mapping to the structure

### Milestone 1 — Contracts and deterministic vertical slice

Create canonical schemas, a minimal FastAPI app, graph validation, a three-agent deterministic workflow, a message gateway, a resource gateway, and basic structured events. UI may be simple. Demonstrate that a blocked message is not delivered and a blocked resource action is not executed.

### Milestone 2 — Visible playground and trace viewer

Add the workflow canvas, per-agent TRSM Node Guard badge, node configuration, actual run statuses and a trace explorer backed by API data.

### Milestone 3 — TRSM intelligence

Add provenance propagation and the three selected threat families. Keep deterministic authorization independent of semantic detector availability.

### Milestone 4 — Metrics and repeatable experiments

Implement literature-grounded CSS/TUE calculations, security/utility/overhead measurements, matched baseline/protected runs and report generation.

### Milestone 5 — Polish and research evidence

Improve dashboard views, run ablations, document failure cases, freeze reproducibility instructions, and provide the research team with sanitized event records and result tables.

---

## 15. Definition of repository readiness

The repository is ready for feature development when:

- [ ] `README.md`, `AGENTS.md`, the master spec and this structure guide agree.
- [ ] One Python dependency/tool configuration and one frontend package manager are selected.
- [ ] Canonical schemas are reviewed by the three developers.
- [ ] A deterministic test can exercise a message from sender → gateway → policy → allow/block → recipient or rejection.
- [ ] A resource action must independently pass the resource gateway.
- [ ] Audit events are emitted for proposals, decisions, and actual delivery/execution outcomes.
- [ ] Tests prove blocked messages do not reach receivers and blocked resource actions do not execute.
- [ ] No secrets or unrestricted tool access are included in the default demo.
- [ ] Evaluation results are linked to scenario, policy, and run versions.
- [ ] The structure remains small enough for the team to understand and maintain.

The purpose of the repository layout is not to maximize the number of folders. It is to make security boundaries, ownership, data contracts, and experimental evidence easy to locate and hard to bypass.
