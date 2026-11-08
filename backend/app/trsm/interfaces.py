from typing import Dict, Any, List
from backend.app.contracts.decisions import PolicyDecision, DecisionType, ThreatFinding
from backend.app.contracts.messages import AgentMessageProposal

class TRSMDecisionEngineInterface:
    """
    Interface agreed upon with Tejasvi.
    Provides pluggable hooks for Tejasvi's Guardian / Decision module.
    """
    def evaluate_agent_message(self, message: AgentMessageProposal, context: Dict[str, Any]) -> PolicyDecision:
        """
        Evaluate an inter-agent message proposal against active security policies.
        Default baseline implementation:
        - Blocks messages containing obvious prompt injections or forbidden exfiltration flags.
        - Allows standard benign communication between authorized peers.
        """
        content_lower = message.content.lower()
        
        # Threat detection baseline
        if any(keyword in content_lower for keyword in ["inject_malicious", "drop table", "ignore previous instructions", "exfiltrate"]):
            return PolicyDecision(
                decision=DecisionType.BLOCK,
                reason_code="PROMPT_INJECTION_OR_UNTRUSTED_INSTRUCTION",
                policy_version="trsm-guardian-v1",
                threat_findings=[
                    ThreatFinding(
                        threat_type="prompt_injection",
                        severity="high",
                        details=f"Forbidden keyword detected in message from {message.sender}"
                    )
                ]
            )
        
        if "quarantine_test" in content_lower:
            return PolicyDecision(
                decision=DecisionType.QUARANTINE,
                reason_code="SUSPICIOUS_PAYLOAD_QUARANTINED",
                policy_version="trsm-guardian-v1"
            )

        if "review_test" in content_lower:
            return PolicyDecision(
                decision=DecisionType.REVIEW,
                reason_code="MANUAL_REVIEW_REQUIRED",
                policy_version="trsm-guardian-v1"
            )

        return PolicyDecision(
            decision=DecisionType.ALLOW,
            reason_code="POLICY_PASSED_BENIGN",
            policy_version="trsm-guardian-v1"
        )

# Default singleton instance (can be swapped with Tejasvi's real engine)
trsm_decision_engine = TRSMDecisionEngineInterface()
