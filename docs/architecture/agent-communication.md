# Agent Communication Architecture

## Flow of an Inter-Agent Message

```text
Agent Node (Sender)
      │
      ▼
Node Guard (Injects trusted runtime metadata: sender_id, run_id, trace_id)
      │
      ▼
TRSM Agent Communication Gateway (backend/app/runtime/communication_gateway.py)
      │
      ├─► Verify sender & recipient registration
      ├─► Validate configured graph edge
      ├─► Check provenance & trust labels
      │
      ▼
Policy Enforcement Engine (backend/app/trsm/policy_engine.py)
      │
      ├─► Consult Runtime Guardian (prompt injection, role hijacking)
      ├─► Check role permissions & peer allowlist
      │
      ▼
Decision: [ALLOW | BLOCK | QUARANTINE | REVIEW]
      │
      ├─► ALLOW:      Deliver payload to Recipient Agent
      ├─► BLOCK:      Drop payload; receiver gets nothing; record reason code
      ├─► QUARANTINE: Isolate payload for inspection; prevent execution
      └─► REVIEW:     Pause execution; await human-in-the-loop signoff
      │
      ▼
Audit Collector: Emit structured causal event (message.delivered or message.blocked)
```

## Key Contracts
- `AgentMessageProposal`: Sender proposal containing payload, target, and trace context.
- `PolicyDecision`: Canonical response containing enum (`ALLOW`, `BLOCK`, `QUARANTINE`, `REVIEW`), reason code, evidence reference, and policy version.
