# Evaluation and Experiment Protocol

## Objective
Empirically measure the security improvements, utility impact, and runtime overhead introduced by TRSM in a multi-agent workflow.

## Experimental Setup
- **Baseline Condition:** The multi-agent workflow executes with direct inter-agent messaging and unrestricted tool invocation.
- **Protected Condition:** The multi-agent workflow executes with TRSM Agent Communication Gateway and Controlled Resource Gateway actively enforcing policy.

## Scenario Suites
1. **Benign Scenarios:** Validate task completion rate, CSS, and legitimate tool utilization under clean conditions.
2. **Adversarial Scenarios:** Validate attack mitigation across prompt injection, memory poisoning, role hijacking, and unauthorized resource access.

## Repeatability Requirements
- Each scenario trial must record:
  - Scenario file and version.
  - Policy configuration version.
  - Model seed / deterministic mock flag.
  - Full trace of emitted audit events.
  - Calculated metrics and raw denominators.
