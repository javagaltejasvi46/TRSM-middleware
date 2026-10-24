# TRSM Middleware: Project Progress & Implementation Roadmap

**Project:** TRSM Middleware for Trust, Risk, and Security Management in LLM-Based Agentic Multi-Agent Systems  
**Status:** Tejasvi's & Yashwanth's Backend & Runtime Modules Complete (~85% – 90% Overall Scope)  
**Active Feature Branch:** `tejasvi-vtemp`  
**Last Updated:** October 2026  
**UI Reference:** [Google Stitch Design Project 1565947815185610243](https://stitch.withgoogle.com/projects/1565947815185610243)

---

## 1. Executive Summary

TRSM is a lightweight runtime mediation layer for LLM-based Agentic Multi-Agent Systems (AMAS). It wraps execution runtimes (specifically LangGraph) to enforce zero-trust security invariants across agent interactions and external resources.

On the `tejasvi-vtemp` branch:
1. **Tejasvi's Core Modules:** Policy Enforcement Engine, Declarative Rules, Runtime Guardian, Threat Detectors, Lineage Tracking & Non-Elevation Guarantees, CSS/TUE Calculators, and the Repeatable Evaluation Harness.
2. **Yashwanth's Core Modules:**
   - **LangGraph StateGraph Integration:** Workflow compilation via `GraphCompiler` into native LangGraph execution with central gateway mediation steps (`gw_A_to_B`) and conditional routing to `END` on blocks.
   - **SQLite Persistence Layer:** Persistent SQLite repositories for Workflows, Runs, Audit Events, and Human-in-the-Loop Reviews using `aiosqlite`.
   - **Server-Side Topology Validator (`GraphValidator`):** Deep validation preventing duplicate nodes, self-loops, missing entry points, and undeclared peer edges.
   - **Sandboxed Tool Registry (`ToolRegistry`):** Sandboxed tool operations, schema listings, rate limits, and fail-closed handling for unregistered tools.
   - **Ollama Local Model Adapter (`OllamaAdapter`):** Model generation, daemon connectivity health check (`check_health()`), and local model catalog query (`list_models()`).
   - **FastAPI Endpoints:** Full CRUD for Workflows (`POST`, `GET`, `PUT`, `DELETE`), Runs (`POST`, `GET`, `GET /status`), Events (filtered query by type, actor, decision), Trace Graph DAG generation, and Human-in-the-Loop Review resolution (`GET /api/reviews`, `POST /api/reviews/{id}/resolve`).

---

## 2. Milestone Progress & Scorecard

| Milestone | Scope & Description | Status | Completion |
|---|---|---|:---:|
| **Milestone 0: Contract Freeze** | Canonical Pydantic schemas, enums, machine reason codes, OpenAPI endpoints | **Completed** | **100%** |
| **Milestone 1: Minimal Vertical Slice** | Inter-agent message proposal, gateway check, policy decision, delivery/block, audit emission | **Completed** | **100%** |
| **Milestone 2: Mandatory Policy Enforcement** | Central Communication Gateway & Controlled Resource Gateway, declarative rules, fail-closed defaults | **Completed** | **100%** |
| **Milestone 3: Audit & Persistence** | SQLite persistence for events, runs, reviews, workflows, structured causal trace DAG, non-elevation | **Completed** | **100%** |
| **Milestone 4: Threat Detection & Scenarios** | Detectors for prompt injection, memory poisoning, role hijacking, versioned YAML benchmark suite | **Completed** | **100%** |
| **Milestone 5: CSS/TUE & Evaluation** | Component Synergy & Tool Efficacy calculators, baseline vs. protected comparison runner, paper reports | **Completed** | **100%** |
| **Milestone 6: LangGraph Runtime Execution** | Native LangGraph StateGraph compiler, AgentRunner, intermediate gateway nodes, sandboxed tools | **Completed** | **100%** |
| **Milestone 7: Visual UI & Realtime Integration** | React Flow playground, node configuration, live runs, Google Stitch design | **In Progress (Debarshi)** | **50%** |

---

## 3. Yashwanth's Implemented Modules (`tejasvi-vtemp` Branch)

### A. LangGraph Runtime Engine (`backend/app/runtime/`)
- [x] **StateGraph Compiler (`graph_compiler.py`):** Compiles user workflows into LangGraph `StateGraph` state machines with inter-agent gateway nodes (`gw_{source}_to_{target}`) that enforce mediation before messages reach target agent context.
- [x] **Agent Execution Lifecycle (`agent_runner.py`):** Wraps model generation (Ollama or deterministic mock), tool request formulation via `NodeGuard`, and proposal creation.
- [x] **Workflow Topology & Peer Validator (`graph_validator.py`):** Deep server-side validation rejecting invalid node IDs, missing roles, duplicate nodes, self-communication loops, and unlisted peer connections.
- [x] **Sandboxed Tool Registry (`tool_registry.py`):** Sandboxed implementations for `customer_db`, `workflow_memory`, `test_suite`, `deployment_manager`, and `code_linter` with schema descriptions and fail-closed defaults.
- [x] **Ollama Local LLM Adapter (`adapters/ollama_adapter.py`):** Async HTTP client with `check_health()`, `list_models()`, and fallback handling to mock adapters for reproducible tests.

### B. SQLite Persistence Layer (`backend/app/persistence/`)
- [x] **Database Schema & Connection (`db.py`):** `aiosqlite` async context manager initializing tables and indexes for `workflows`, `runs`, `audit_events`, and `reviews`.
- [x] **Workflow Repository (`workflow_repository.py`):** SQLite CRUD (`save`, `get`, `list_all`, `delete`).
- [x] **Run Repository (`run_repository.py`):** Execution run lifecycle persistence (`create_run`, `update_run`, `get_run`, `list_runs`).
- [x] **Event Repository (`event_repository.py`):** Structured audit event storage and multi-criteria query filtering (`event_type`, `actor_id`, `policy_decision`).
- [x] **Review Repository (`review_repository.py`):** Human-in-the-Loop review management (`create_review`, `list_pending_reviews`, `resolve_review`).

### C. FastAPI Endpoints & Services (`backend/app/api/`)
- [x] **Workflows API (`routes/workflows.py`):** Full CRUD (`POST /api/workflows`, `GET /api/workflows`, `GET /api/workflows/{id}`, `PUT /api/workflows/{id}`, `DELETE /api/workflows/{id}`, `POST /api/workflows/validate`).
- [x] **Runs API (`routes/runs.py`):** Run execution (`POST /api/runs`, `GET /api/runs`, `GET /api/runs/{id}`, `GET /api/runs/{id}/status`).
- [x] **Events & Traces API (`routes/events.py`):** Filtered event queries and DAG trace generation (`GET /api/runs/{id}/events`, `GET /api/runs/{id}/trace`).
- [x] **Human Review API (`routes/reviews.py`):** HITL review resolution (`GET /api/reviews`, `GET /api/reviews/{id}`, `POST /api/reviews/{id}/resolve`).
- [x] **Metrics & Evaluations API (`routes/metrics.py`):** CSS, TUE, and run comparisons (`GET /api/runs/{id}/metrics`, `GET /api/evaluations/compare`).

---

## 4. Automated Verification Results

### Pytest Full Suite: **54/54 Tests Passing** in ~2.28s (`python -m pytest backend/tests -v`)
- `test_routes.py` & `test_routes_extended.py`: 8 tests covering health, full workflows CRUD, runs listing/status, events filtering, trace DAG, reviews, and evaluations.
- `test_gateways.py`: 2 tests covering communication and resource gateway mediation.
- `test_persistence.py`: 4 tests covering SQLite repositories for workflows, runs, events, and reviews.
- `test_graph_compiler.py`: 2 tests covering LangGraph StateGraph clean execution and prompt injection blocking.
- `test_graph_validator.py`: 5 tests covering topology checks, duplicate node detection, self-loop rejection, and peer warnings.
- `test_agent_runner.py`: 2 tests covering tool execution and shell command blocking.
- `test_policy_engine.py`: 13 tests covering deterministic rules, threat findings, and fail-closed invariants.
- `test_provenance.py`: 4 tests covering multi-hop lineage, merge taint, and non-elevation.
- `test_runtime_guardian.py`: 5 tests covering threat detectors and benign controls.
- `test_evaluation_runner.py` & `test_metrics.py`: 6 tests covering CSS, TUE, ASR, FPR, FNR, and performance percentiles.
- `test_schemas.py`: 3 tests covering core Pydantic contracts.

### Empirical Evaluation Benchmark Results (`python scripts/run_evaluation.py`):
- **Scenarios Evaluated:** 8 versioned scenarios (6 Adversarial, 2 Benign)
- **Baseline ASR:** 100.0% (6/6 attacks succeeded)
- **TRSM Protected ASR:** 0.0% (0/6 attacks succeeded — 100% neutralized)
- **False Positive Rate (FPR):** 0.0% on clean control tasks
- **Mean Added Overhead:** +4.9ms (6.5%)
- **Evaluation Report:** Persisted in `artifacts/evaluation_report.md`.

---

## 5. Next Steps for Frontend Integration (Debarshi)

1. Align the React Flow canvas with the [Google Stitch UI project](https://stitch.withgoogle.com/projects/1565947815185610243).
2. Connect the React Flow canvas directly to `/api/workflows` to load and save configurations.
3. Wire the "Run Workflow" button to `POST /api/runs` and poll `GET /api/runs/{id}/status`.
4. Render causal trace execution nodes and edge badges from `GET /api/runs/{id}/trace`.
5. Display live metric cards (CSS, TUE, ASR, latency) from `GET /api/runs/{id}/metrics`.
