# Literature Survey: Trust, Risk, and Security Management in Agentic AI

## Overview
Recent advancements in Large Language Model (LLM) agents have enabled autonomous workflows, tool use, and multi-agent coordination. However, this autonomy introduces significant vulnerabilities:
1. **Prompt Injection Propagation:** Adversarial instructions embedded in external inputs or peer messages hijack agent intent.
2. **Memory Poisoning:** Malicious updates to shared memory or vector stores compromise future runs.
3. **Privilege Escalation & Confused Deputy:** Compromised agents exploit higher-privileged peer agents or unrestricted tool interfaces.

## Key Foundational Concepts
- **Policy Enforcement Points (PEP):** Intercepting requests before they reach target resources (NIST SP 800-207 Zero Trust).
- **Provenance & Information Flow Control:** Labeling untrusted sources and tracking data flows across multi-hop reasoning.
- **Agentic Metrics:**
  - **Component Synergy Score (CSS):** Measures coordination efficiency and communication effectiveness across agent teams.
  - **Tool Utilization Efficacy (TUE):** Measures ratio of productive, authorized tool operations versus failed/redundant calls.
