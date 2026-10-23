# Research Gap: Architectural Security in Multi-Agent Workflows

## Current State of the Art
- Most LLM security solutions focus on single-agent input guardrails (e.g., Llama Guard, NeMo Guardrails) or prompt sanitization.
- Agent benchmarks primarily evaluate single-turn jailbreaks or standalone tool-calling accuracy.

## Identified Gaps
1. **Lack of Mandatory Inter-Agent Mediation:** Existing multi-agent frameworks (AutoGen, CrewAI) allow unrestricted agent-to-agent message passing by default.
2. **Coupled Tool Authorization:** Tool permissions are often tied to agent prompts rather than deterministic backend policy engines.
3. **Absence of Causal Multi-Hop Provenance:** When an attack succeeds across a 4-agent chain, tracing the root cause and initial prompt contamination is difficult.
4. **Scarcity of Utility-Security Tradeoff Studies:** Few empirical studies measure the overhead (latency, token cost, task completion rate) of adding security middleware to multi-agent graphs.

TRSM bridges these gaps with a concrete prototype and repeatable evaluation methodology.
