# Operational Guidelines for AI Coding Agents in TRSM

These rules apply to all AI coding agents (such as Claude Code, Antigravity, GitHub Copilot) working in this repository.

## 1. Primary Invariants (Non-Negotiable)

1. **Mandatory Inter-Agent Mediation**: Every proposed message from one agent to another must be evaluated by the backend **TRSM Agent Communication Gateway** (`backend/app/runtime/communication_gateway.py`) and authorized by the **Policy Engine** (`backend/app/trsm/policy_engine.py`) before delivery. Never introduce a direct agent-to-agent shortcut.
2. **Mandatory Resource Mediation**: Every tool, database, or memory action must pass through the **Controlled Resource Gateway** (`backend/app/runtime/resource_gateway.py`) and receive independent authorization. A permitted message does not grant tool permissions.
3. **Frontend is Not a Security Boundary**: The frontend (`frontend/`) visualizes configuration, runtime node status, and audit traces. Never rely on client-side state, React Flow edges, or badges as proof of authorization.
4. **Authoritative Decisions**: Only the Policy Engine can emit `ALLOW`, `BLOCK`, `QUARANTINE`, or `REVIEW`. A detector emits findings; it cannot grant capability. Fail closed on unknown agents, unknown tools, or malformed requests.
5. **Canonical Contracts**: The backend Pydantic schemas in `backend/app/schemas/` are the single source of truth for wire contracts. Do not introduce competing schemas.

## 2. Coding Principles

- **Inspect Before Changing**: Inspect the existing directory structure and existing code before creating or moving files.
- **Scope Bounded Changes**: Work within your assigned files/modules. Never do silent refactors of unrelated code or public schemas.
- **Provenance Integrity**: Preserve source event references, parent event IDs, and trust labels (`trusted_policy`, `user_input`, `untrusted_external`, `agent_generated`, `tool_result`, `validated`). Never silently elevate untrusted data to trusted.
- **Evidence-Based Evaluation**: Never invent CSS or TUE formulas or fabricate test/experiment numbers. Record metrics strictly from actual scenario runs.
- **Comprehensive Testing**: When implementing rules or gateways, provide test cases for:
  - Allowed requests
  - Forbidden/blocked requests
  - Malformed or incomplete requests
  - Unknown agents/tools
  - Benign requests resembling attacks
  - Gateway bypass attempts

## 3. Reporting Verification

Always report:
1. Exact commands executed.
2. Direct test outputs and status.
3. Any untested boundaries or limitations.
