# TRSM Detailed Module Design

## Module Responsibilities

### 1. `backend/app/runtime`
- `communication_gateway.py`: Mediates inter-agent message envelopes. Validates registered sender and recipient, loads context, calls Policy Engine, and only delivers if decision is `ALLOW`.
- `resource_gateway.py`: Mediates tool calls and memory accesses. Validates against schema, checks permissions, checks argument risk, calls Policy Engine, and executes registered handlers.
- `orchestrator.py`: Orchestrates node step progression using compiled LangGraph state machines.
- `agent_runner.py`: Wraps agent LLM/mock invocations, capturing input/output proposals.
- `tool_registry.py`: Holds registry of authorized mock and safe tools.

### 2. `backend/app/trsm`
- `policy_engine.py`: Core deterministic rule engine evaluating permissions and threat findings.
- `runtime_guardian.py`: Detector coordinator analyzing payloads across threat families.
- `provenance.py`: Lineage tracking ensuring untrusted inputs are not upgraded to trusted.
- `detectors/`:
  - `prompt_injection.py`: Heuristic & pattern matching for instruction override / jailbreaks.
  - `memory_poisoning.py`: Integrity validation on proposed memory state updates.
  - `role_hijacking.py`: Checks for unauthorized role assumption or orchestrator override.

### 3. `backend/app/audit`
- `event_collector.py`: Asynchronously persists structured audit events to SQLite.
- `trace_builder.py`: Reconstructs the DAG of execution events for frontend and evaluation consumers.
- `redaction.py`: Sanitizes credentials, sensitive tokens, and full raw prompts.
