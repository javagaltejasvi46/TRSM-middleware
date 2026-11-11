# TRSM Middleware Backend & Execution Runtime

Backend execution engine and security gateway for the **TRSM (Trust-Region Security Middleware)** multi-agent playground.

## Architecture Highlights
- **FastAPI Backend**: Exposes REST endpoints for workflows, runs, events, and metrics.
- **Server-Side Workflow Validation**: Strict graph integrity verification; enforces declared roles, models, and explicit `allowed_peers` boundaries.
- **LangGraph Runtime Engine**: Compiles validated graph definitions into executable multi-agent state machines.
- **Central Agent Communication Gateway**: Mandatory mediation boundary where inter-agent messages are inspected, audited, and enforced (`ALLOW`, `BLOCK`, `QUARANTINE`, `REVIEW`).
- **Resource Gateway**: Enforces role allowlists and sandboxing over tool, database, and memory operations (arbitrary shell/filesystem operations blocked by default).
- **SQLite Audit Event Persistence**: Complete causal tracking across all 14 core event fields with granular query filtering.

---

## Quickstart

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run the Development Server
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **OpenAPI Schema**: `docs/openapi.json` or [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### 3. Run Automated Tests
```bash
pytest
```
Runs all 31 unit and integration tests across routers, validators, runtime, gateways, and persistence.

### 4. Run the End-to-End Demo Script
```bash
python scripts/run_demo.py
```

---

## API Summary

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Health check endpoint |
| `/api/workflows` | `POST` / `GET` | Create, list, and validate multi-agent workflow definitions |
| `/api/workflows/{wf_id}` | `GET` / `PUT` | Retrieve and update workflow configurations |
| `/api/workflows/validate` | `POST` | Dry-run server-side graph validation without saving |
| `/api/runs` | `POST` / `GET` | Launch a LangGraph workflow execution and inspect run status |
| `/api/runs/{run_id}` | `GET` | Get detailed node execution history and state |
| `/api/events` | `GET` | Query structured audit events (filter by `run_id`, `actor_id`, `event_type`, `policy_decision`) |
| `/api/events/{event_id}` | `GET` | Fetch individual audit event record |

---

## Integration Contracts
- **Tejasvi (Security & Guardian)**: Pluggable decision engine in `backend/app/trsm/interfaces.py` (`evaluate_agent_message`, `evaluate_resource_action`).
- **Debarshi (Frontend Playground)**: Standardized OpenAPI specification in `docs/openapi.json`.
