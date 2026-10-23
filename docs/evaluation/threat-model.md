# TRSM Threat Model

## Assumed Adversary Capabilities

1. **Untrusted External Data:** The adversary can inject arbitrary prompt sequences via user requests or mock external data feeds.
2. **Compromised Intermediate Agent:** The adversary may successfully manipulate an upstream agent (e.g., Backend Agent) into generating adversarial tool calls or forwarding malicious messages.
3. **Privilege Escalation Attempts:** An agent may attempt to address an unauthorized peer or execute tools outside its designated role scope.
4. **Memory Manipulation:** An agent may attempt to persist unverified instructions into long-term or shared memory.

## Out of Scope
- Compromise of host OS or container runtime.
- Physical / hardware side-channel attacks on LLM accelerators.
- Malicious tampering with backend configuration files or database directly outside the application boundary.
