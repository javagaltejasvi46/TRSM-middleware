# Audit and Instrumentation Specification

## Overview

The audit pipeline provides a structured, causal stream of events spanning all agent executions, message proposals, policy decisions, and resource operations.

## Event Schema Identity Fields

- `event_id`: Unique identifier (UUID4) for each immutable event.
- `run_id`: Execution scope identifier.
- `trace_id`: Correlation identifier for related execution branches.
- `parent_event_id`: Causal ancestor identifier, enabling graph reconstruction of attacks.
- `timestamp`: UTC timestamp (ISO 8601).
- `actor_id`: Node or service that initiated the event.
- `target_id`: Intended recipient or resource.
- `event_type`: Categorized event (e.g., `message.proposed`, `message.policy_decided`, `message.delivered`, `resource.executed`, `threat.detected`).
- `policy_decision`: `ALLOW`, `BLOCK`, `QUARANTINE`, or `REVIEW`.
- `reason_code`: Machine-readable reason (e.g., `PEER_NOT_ALLOWED`, `PROMPT_INJECTION_DETECTED`).
- `provenance`: Trust labels and origin chain.
- `duration_ms`: Processing latency for overhead calculation.

## Privacy and Redaction
- Raw prompts and system instructions are redacted or summarized before persistence.
- Secret credentials or private environment tokens are blocked from audit logs via the `redaction` utility.
