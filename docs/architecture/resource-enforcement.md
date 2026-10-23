# Controlled Resource Enforcement

## Resource Gateway Pattern

Agents often need access to tools, databases, APIs, and shared memory. Directly handing tool functions or database connections to an LLM agent exposes the system to prompt injection, data exfiltration, and unauthorized writes.

All resource operations must be routed through `backend/app/runtime/resource_gateway.py`.

```text
Agent Node requests Tool / Database / Memory Action
      │
      ▼
Controlled Resource Gateway (backend/app/runtime/resource_gateway.py)
      │
      ├─► Validate requested resource name against registered tools
      ├─► Validate action arguments against defined schemas
      ├─► Check agent role authorization for the requested operation
      │
      ▼
Policy Engine Checks
      │
      ├─► Check memory poisoning / unauthorized write detector
      ├─► Check argument sanitization & rate limits
      │
      ▼
Decision:
      ├── ALLOW     ──► Execute adapter (mock DB, sandbox tool, safe memory)
      │                   │
      │                   ▼
      │                 Return result with attached provenance label
      └── NON-ALLOW ──► Halt execution; raise security violation; emit audit event
```

## Isolation Rules
1. Communication permission does not equal resource capability.
2. Default deny for unknown tools or arguments outside Pydantic schema validation.
3. Every executed resource operation attaches a `tool_result` provenance label before returning output to the requesting agent.
