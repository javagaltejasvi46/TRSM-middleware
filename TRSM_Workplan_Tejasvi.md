# TRSM Development Workplan — Tejasvi

**Role:** AI Engineering, Data Engineering, TRSM decision logic and evaluation  
**Primary ownership:** The security intelligence behind the middleware: policy decisions, provenance, runtime threat detection, CSS/TUE instrumentation logic, and reproducible evaluation.

## 1. Project context

We are building a visual, n8n-like playground for configuring and running a LangGraph-based multi-agent workflow. The demonstration workflow will include agents such as Backend, DB Manager, QA and DevOps. Each agent visibly carries a **TRSM Node Guard**, while a central **TRSM Agent Communication Gateway** intercepts every agent-to-agent message. Tool, database and memory operations pass through a separate resource gateway. The system records audit events and computes security and performance results.

The intended end-to-end path is:

`Agent message/action proposal → Gateway → policy and threat checks → ALLOW / BLOCK / QUARANTINE / REVIEW → receiver or resource → audit event → metrics`

The gateway is enforced in the backend. The UI's node guard is a visual representation/configuration surface, not a security boundary.

## 2. Your owned modules

### A. Policy decision engine

Implement the reusable decision logic called by Yashwanth's gateway. Keep critical decisions deterministic wherever possible.

Responsibilities:
- Define policy context for sender, receiver, agent role, allowed peers, requested action, tool/resource scope, provenance labels, run state and policy version.
- Evaluate peer permissions and role-scoped permissions.
- Return a structured decision: `ALLOW`, `BLOCK`, `QUARANTINE`, or `REVIEW`.
- Return a machine-readable reason code plus concise evidence; do not return an unexplained boolean.
- Fail closed for unknown agents, unknown tools, malformed requests and missing required policy data.
- Keep rules configurable and test each rule independently.

### B. Provenance and trust labels

Implement the logic that tracks where content originates and how it moves between agents and memory.

Suggested initial labels:
- `trusted_policy`
- `user_input`
- `untrusted_external`
- `agent_generated`
- `tool_result`
- `validated`

These labels indicate origin and validation status; they do **not** prove that a message is safe. Preserve source-event references and parent/lineage links when content is passed to another agent. Do not silently upgrade external content to trusted because an agent summarised or repeated it.

### C. Runtime Guardian

Implement the initial threat-detection module for three agreed attack families:
1. Prompt-injection propagation through agent messages.
2. Memory poisoning or suspicious memory writes.
3. Role/orchestrator hijacking and attempts to exceed an agent's authority.

Use deterministic checks for structural violations and permissions; use semantic detection only as an additional signal. The guardian should emit findings such as `threat_type`, `severity`, `confidence`, `source_event_id`, `evidence`, and `recommended_action`. It must not execute tools or alter trusted policy itself.

### D. Metrics and evaluation harness

Implement the calculation layer for:
- CSS (Component Synergy Score)
- TUE (Tool Utilization Efficacy)
- Attack Success Rate (ASR)
- False-positive and false-negative rates
- Clean-task and adversarial-task success
- Added latency and estimated/model/tool cost

**Important:** obtain the exact CSS/TUE definitions and any published operationalization from the literature/research team before coding the formulas. Do not invent a formula and describe it as the paper's definition. If the published definition is underspecified for our runtime data, document the chosen operationalization as our implementation and keep the raw component measurements available.

Create a repeatable evaluation runner that can execute the same scenarios with TRSM disabled (baseline) and enabled (protected). Store per-trial outcomes, not just averages. Include benign scenarios so we can measure harmful blocking as well as attack prevention.

## 3. Suggested code ownership

```text
backend/trsm/
  policy_engine.py
  provenance.py
  runtime_guardian.py
  metrics.py
  evaluation/
    scenarios.py
    runner.py
    reports.py
  tests/
    test_policy_engine.py
    test_provenance.py
    test_runtime_guardian.py
    test_metrics.py
```

Adapt this to the repository once Yashwanth creates the shared package layout. Avoid editing the API contracts independently; propose changes and agree them with Yashwanth before merging.

## 4. Required interfaces with Yashwanth

Agree and test these contracts before detailed implementation:

```python
evaluate_agent_message(message, context) -> PolicyDecision
evaluate_resource_action(action, context) -> PolicyDecision
track_provenance(content, source_event) -> ProvenanceRecord
detect_threat(event, recent_trace) -> list[ThreatFinding]
calculate_css(run_trace) -> MetricResult
calculate_tue(run_trace) -> MetricResult
```

These are conceptual signatures; use the agreed Pydantic types from the backend contract. A `PolicyDecision` must include `decision`, `reason_code`, `policy_version`, and relevant evidence. Yashwanth owns routing and persistence; you own the decision/detection/metric logic.

## 5. Milestones and acceptance criteria

### Milestone 1 — Rules and contracts
- Review the event/message/action schemas with Yashwanth.
- Implement unit-tested allow/deny checks for role, peer, tool and resource permissions.
- Demonstrate fail-closed behaviour for unknown identities and malformed inputs.

### Milestone 2 — Provenance and threat findings
- Provenance survives at least two agent-to-agent hops.
- An injected instruction remains marked as untrusted when relayed or summarised, where lineage is available.
- All three threat families have positive and benign/negative test cases.
- Findings include a source event and a structured reason.

### Milestone 3 — Metrics
- CSS/TUE calculations have documented inputs, outputs, assumptions and tests.
- ASR, FPR and FNR definitions are explicit and denominators are correct.
- Metrics distinguish an attack being detected from its actual objective being prevented.
- Baseline and protected runs use the same scenario definitions.

### Milestone 4 — Evaluation evidence
- Provide reproducible scenarios, seed/configuration where applicable, run artifacts and a generated comparison report.
- Report security and utility together; do not declare success solely because more operations are blocked.
- Document limitations and failed cases for the research-paper team.

## 6. Shared engineering rules

- Every inter-agent message must be routed through the central gateway; do not add direct agent-to-agent shortcuts.
- Tools, databases and memory must be accessed through the resource gateway and checked separately from message permissions.
- Emit structured events; do not make the metrics engine scrape human-readable logs.
- Do not log secrets or unrestricted raw payloads by default. Prefer redacted summaries and payload references.
- The frontend must never be the authority for security decisions.
- Add tests with each feature. Do not claim a test or experiment passed unless it was executed.

## 7. Agentic development workflow

Use a coding agent to accelerate focused tasks, but keep control of architecture and correctness:
1. Start each task with a short plan and acceptance criteria.
2. Give the coding agent one bounded module/task, relevant contracts and test expectations.
3. Ask it to inspect existing code before editing and to avoid unrelated refactors.
4. Review every diff, especially authorization branches, trust-label transitions and metric formulas.
5. Run tests and inspect generated report data yourself.
6. Commit small, reviewable changes on a feature branch; do not let an agent silently change shared interfaces.

Useful task prompt:

> Inspect the existing TRSM contracts and implement only `[module/feature]`. Preserve the agreed public interfaces. Add unit tests for allowed, denied, malformed, and edge-case inputs. Do not change unrelated files. Explain assumptions and list commands/tests actually executed.

## 8. Handoff to the research-paper team

Provide the researchers with:
- exact metric definitions and operational assumptions;
- attack/benign scenario catalogue;
- baseline-versus-protected trial records;
- ASR/FPR/FNR, task success, CSS/TUE and latency/cost outputs;
- limitations, failed cases and reproducibility instructions.

Your success criterion is not merely a working detector; it is a testable, auditable TRSM decision layer whose impact can be measured.
