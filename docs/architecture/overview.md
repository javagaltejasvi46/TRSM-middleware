# Architecture Overview: TRSM Middleware

TRSM (Trust, Risk, and Security Management) Middleware provides a runtime mediation layer for LLM-based multi-agent workflows.

## System Model

In a standard agentic system, agents communicate directly with peer agents and invoke arbitrary tools or write to shared memory without centralized inspection.

TRSM introduces two critical runtime mediation boundaries:
1. **TRSM Agent Communication Gateway:** Intercepts, inspects, and authorizes every proposed message between agents.
2. **Controlled Resource Gateway:** Intercepts, inspects, and authorizes every external tool call, database query, and shared memory write.

## Non-Negotiable Invariants

- **Fail-Closed Default:** Unrecognized agents, undeclared graph edges, unauthorized tools, or malformed proposals immediately result in `BLOCK` decisions.
- **Independent Resource Authorization:** An authorized message between agents does not grant capability to invoke tools.
- **Frontend as Client Only:** The browser playground renders visual node guards, edges, and trace streams, but holds zero authorization authority.
- **Causal Auditability:** Every action is linked via `run_id`, `trace_id`, `event_id`, and `parent_event_id` to form a tamper-evident audit trail.

## Module Boundaries

- `frontend/`: Visual workflow builder, run execution view, trace explorer, and evaluation dashboard.
- `backend/app/runtime/`: Orchestration, gateway routing, node guard instrumentation, and tool adapters.
- `backend/app/trsm/`: Policy enforcement engine, threat detection (injection, poisoning, hijacking), and provenance tracking.
- `backend/app/audit/`: Structured audit event collection, redaction, and persistence.
- `backend/app/evaluation/`: CSS, TUE, ASR, latency, and baseline/protected experiment execution.
