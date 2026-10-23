# TRSM Middleware: Project Progress & Implementation Roadmap

**Project:** TRSM Middleware for Trust, Risk, and Security Management in LLM-Based Agentic Multi-Agent Systems  
**Status:** Pre-MVP & Foundational Scaffolding Complete (~55% – 60% Overall Scope)  
**Last Updated:** October 2026  
**UI Reference:** [Google Stitch Design Project 1565947815185610243](https://stitch.withgoogle.com/projects/1565947815185610243)

---

## 1. Executive Summary

TRSM is a lightweight runtime mediation layer for LLM-based Agentic Multi-Agent Systems (AMAS). It wraps execution runtimes (such as LangGraph) to enforce zero-trust security invariants across agent interactions and external resources.

The project currently has **100% of its core architecture, canonical schemas, deterministic gateways, and end-to-end vertical slice completed and verified with automated test suites**. The next phase centers on the interactive React Flow visual canvas (referencing the Google Stitch design project), LangGraph state machine binding, live local LLM inference (Ollama), and large-scale empirical evaluation for the research paper.

---

## 2. Milestone Progress & Scorecard

| Milestone | Scope & Description | Status | Completion |
|---|---|---|:---:|
| **Milestone 0: Contract Freeze** | Canonical Pydantic schemas, enums, machine reason codes, OpenAPI endpoints | **Completed** | **100%** |
| **Milestone 1: Minimal Vertical Slice** | Inter-agent message proposal, gateway check, policy decision, delivery/block, audit emission | **Completed** | **95%** |
| **Milestone 2: Mandatory Policy Enforcement** | Central Communication Gateway & Controlled Resource Gateway, fail-closed defaults | **Operational** | **80%** |
| **Milestone 3: Audit & Provenance** | Structured causal trace DAG, lineage tracking, secret redaction engine | **Operational** | **70%** |
| **Milestone 4: Threat Detection & Scenarios** | Detectors for prompt injection, memory poisoning, role hijacking, versioned YAMLs | **In Progress** | **55%** |
| **Milestone 5: CSS/TUE & Evaluation** | Component Synergy & Tool Efficacy calculators, baseline vs. protected comparisons | **In Progress** | **50%** |
| **Milestone 6: Visual UI & Research Evidence** | React Flow playground, node configuration, live runs, evaluation tables for paper | **In Progress** | **45%** |

---

## 3. Detailed Breakdown of Completed Work

### A. Canonical Data Contracts (`backend/app/schemas/`)
- [x] **Authoritative Decisions (`policy.py`):** Strictly typed `ALLOW`, `BLOCK`, `QUARANTINE`, `REVIEW` enum with structured evidence.
- [x] **Trust & Provenance (`provenance.py`):** Causal trust labels (`trusted_policy`, `user_input`, `untrusted_external`, `agent_generated`, `tool_result`, `validated`) with lineage paths.
- [x] **Agent Configurations (`agent.py`):** Role definitions (`backend`, `db_manager`, `qa`, `devops`, `custom`), timeouts, call limits, and peer/tool permissions.
- [x] **Workflow Models (`workflow.py`):** Node graphs, configured edges, and server-side validation models.
- [x] **Message Envelopes (`messages.py`):** Immutable message proposals and delivery envelopes.
- [x] **Controlled Resources (`resources.py`):** Tool calls, database queries, and memory access request/result schemas.
- [x] **Threat Findings (`threats.py`):** Severity classifications and structured evidence models.
- [x] **Audit Telemetry (`events.py`):** Event types (`message.proposed`, `message.delivered`, `message.blocked`, `resource.executed`, `resource.blocked`).
- [x] **Metrics (`metrics.py`):** Component Synergy Score (CSS), Tool Utilization Efficacy (TUE), and run summaries.
- [x] **Frontend TypeScript Mirror (`frontend/src/types/index.ts`):** 100% synchronized wire contracts.

### B. Security Middleware & Gateways (`backend/app/runtime/` & `trsm/`)
- [x] **Central Agent Communication Gateway (`communication_gateway.py`):** Intercepts every inter-agent message proposal; fails closed on unknown peers; ensures blocked payloads never reach recipients.
- [x] **Controlled Resource Gateway (`resource_gateway.py`):** Intercepts and authorizes tool calls, database operations, and memory modifications independently of communication authorization.
- [x] **Policy Enforcement Engine (`policy_engine.py`):** Authoritative policy decision-maker emitting machine-readable reason codes and evidence.
- [x] **Runtime Guardian & Threat Detectors (`detectors/`):**
  - Heuristic instruction override and prompt injection detector (`prompt_injection.py`).
  - Shared memory poisoning and override detector (`memory_poisoning.py`).
  - Unauthorized role assumption and orchestrator hijacking detector (`role_hijacking.py`).
- [x] **Node Guard Runtime Wrapper (`node_guard.py`):** Injects execution context, run IDs, trace IDs, and cryptographic metadata into agent proposals.
- [x] **Safe Tool Registry (`tool_registry.py`):** Sandboxed implementations of customer database, mock test suite, deployment manager, and workflow memory.

### C. Audit & Evaluation Pipeline (`backend/app/audit/` & `evaluation/`)
- [x] **Asynchronous Event Collector (`event_collector.py`):** Collects structured audit events with microsecond timestamps and causal parent links.
- [x] **Sensitive Token Redaction (`redaction.py`):** Strips credentials, API tokens, and secret keys before audit storage.
- [x] **Trace DAG Reconstructor (`trace_builder.py`):** Reconstructs execution graphs for frontend inspection.
- [x] **Metrics Engine (`css.py`, `tue.py`):** Implements literature-grounded Component Synergy Score and Tool Utilization Efficacy calculations.
- [x] **Baseline vs. Protected Comparison (`evaluation_service.py`):** API route to compare matched baseline and protected trials.

### D. Automated Tests & Verification
- [x] **12/12 Automated Pytest Tests Passing:**
  - `test_policy_decision_enum` & `test_trust_labels`
  - `test_allowed_peer_communication` & `test_blocked_unauthorized_peer`
  - `test_blocked_prompt_injection` & `test_blocked_unauthorized_tool`
  - `test_communication_gateway_blocks_undelivered_message` (proves receiver gets nothing upon block)
  - `test_resource_gateway_executes_allowed_action`
  - `test_health_endpoint`, `test_validate_workflow_endpoint`, `test_start_run_and_get_metrics`
- [x] **Deterministic CLI Demonstration Runner (`scripts/run_demo.py`):**
  - Benign scenario executes cleanly with 0 blocked actions.
  - Adversarial prompt injection scenario is immediately intercepted and blocked by the Central Gateway (1 blocked action).
  - Baseline mode reproduces vulnerability with 0 blocked actions under identical attack input.

### E. Frontend Visual Scaffolding (`frontend/`)
- [x] **UI Design System (`src/index.css`):** Sleek dark theme, glassmorphism panels, glowing status badges, and typography (Inter & JetBrains Mono).
- [x] **Visual Components:**
  - `AgentNode`: Node card with dynamic peer and tool permission indicators.
  - `TrsmNodeGuardBadge`: Visual per-node protection badge with active status.
  - `GatewayNode`: Central visual mediation gateway node.
  - `RunControls`: Scenario selector, custom task input, and TRSM protection toggle.
  - `TraceExplorer`: Chronological audit stream with `ALLOW`, `BLOCK`, `QUARANTINE`, and `REVIEW` badges.
  - `MetricsPanel`: Live cards for CSS, TUE, blocked attack count, and latency overhead.
- [x] **Pages:**
  - `PlaygroundPage`: Canvas orchestrator and execution view.
  - `EvaluationPage`: Comparative baseline vs. protected metrics dashboard.
- [x] **Typed API Clients:** Endpoints for `/api/workflows`, `/api/runs`, `/api/runs/{id}/events`, `/api/runs/{id}/metrics`.

### F. Versioned Evaluation Scenarios (`scenarios/`)
- [x] `benign/backend_to_db_allowed.yaml` & `benign/qa_read_test_result.yaml`
- [x] `prompt_injection/direct_instruction_override.yaml` & `prompt_injection/propagated_external_instruction.yaml`
- [x] `memory_poisoning/untrusted_memory_write.yaml`
- [x] `role_hijacking/unauthorized_role_change.yaml`
- [x] `resource_authorization/unknown_tool.yaml` & `resource_authorization/write_without_permission.yaml`

---

## 4. Work Yet to Be Done (Next Steps)

### 1. Frontend & Visual Polish (Debarshi)
- [ ] **Google Stitch Design Integration:** Adapt UI components and layouts to align with the visual reference in [Google Stitch Project 1565947815185610243](https://stitch.withgoogle.com/projects/1565947815185610243).
- [ ] **Interactive React Flow Canvas:** Run `npm install` in `frontend/` and wire interactive node dragging, edge creation, and connection validation to `@xyflow/react`.
- [ ] **Dynamic Edge States:** Visually distinguish configured graph edges from runtime approved/blocked message hops during live execution.
- [ ] **Real-time Streaming:** Evaluate Server-Sent Events (SSE) or WebSockets for live streaming of node state transitions.

### 2. Runtime & LangGraph Compilation (Yashwanth)
- [ ] **LangGraph StateGraph Integration:** Compile validated `WorkflowConfig` into LangGraph execution graphs with cyclical state transitions.
- [ ] **Ollama Local LLM Support:** Validate live inference with local models (e.g. `llama3:8b`, `mistral`) through `ollama_adapter.py`.
- [ ] **SQLite Repository Layer:** Transition in-memory run caches to persistent database tables via `db.py`.
- [ ] **Human-in-the-Loop Review Endpoint:** Complete the approval/rejection state machine for `REVIEW` decisions (`/api/reviews/{id}/resolve`).

### 3. TRSM Security & Advanced Detection (Tejasvi)
- [ ] **Semantic Embedding / Classifier Scanners:** Supplement regex/heuristic detectors with optional lightweight embedding-based similarity checks.
- [ ] **Cryptographic Hash Chaining:** Implement SHA-256 hash chaining across consecutive audit events to guarantee verifiable tamper resistance.
- [ ] **Multi-Hop Provenance Propagation:** Test deeper agent chains (4+ hops) to verify untrusted labels do not elevate during complex summarization loops.

### 4. Empirical Evaluation & Research Paper (Research Team + Tejasvi)
- [ ] **Statistical Benchmark Suite:** Run 20+ trials per scenario in both Baseline (unmediated) and Protected (TRSM) modes.
- [ ] **Metric Aggregation:** Compile empirical data for Attack Success Rate (ASR), False Positive Rate (FPR), False Negative Rate (FNR), CSS, TUE, and latency distribution ($p_{50}, p_{90}, p_{99}$).
- [ ] **Research Artifact Generation:** Export sanitized JSONL trace files to `artifacts/` for inclusion in the academic paper submission.
