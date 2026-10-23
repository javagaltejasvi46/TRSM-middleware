# TRSM System Design

## Architecture Blueprint

The TRSM system consists of the following key subsystems:

1. **Frontend Playground:**
   - React Flow visual workflow editor (`@xyflow/react`).
   - Node configuration inspector for agent roles, models, and permissions.
   - Run controls for initiating deterministic or LLM runs.
   - Trace explorer displaying causally linked audit streams.
   - Metrics view showing CSS, TUE, ASR, latency, and token overhead.

2. **Backend API & Orchestration (Yashwanth):**
   - FastAPI application providing `/api/workflows`, `/api/runs`, `/api/events`, `/api/metrics`.
   - Graph validation ensuring valid DAG topology and safe edge configurations.
   - LangGraph compiler transforming graph configurations into runtime nodes.
   - SQLite persistent storage for workflows, runs, events, and metrics.

3. **TRSM Security Core (Tejasvi):**
   - **Central Communication Gateway:** Intercepts message proposals, extracts metadata, verifies permissions.
   - **Controlled Resource Gateway:** Sanitizes tool arguments and executes registered mock or sandboxed tools.
   - **Policy Engine:** Evaluates declarative rules, fails closed, and emits structured decisions (`ALLOW`, `BLOCK`, `QUARANTINE`, `REVIEW`).
   - **Runtime Guardian:** Analyzes payloads for prompt injection, memory poisoning, and role escalation.
   - **Provenance Engine:** Tracks data lineage and assigns trust labels.

4. **Telemetry & Evaluation:**
   - Causal audit stream logging all actions with microsecond timestamps and parent links.
   - Repeatable baseline vs. protected evaluation harness.
