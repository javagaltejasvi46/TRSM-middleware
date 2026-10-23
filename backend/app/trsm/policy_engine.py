"""Authoritative TRSM Policy Enforcement Engine."""

from typing import List, Optional
from ..schemas.messages import AgentMessageProposal
from ..schemas.policy import PolicyDecision, PolicyDecisionEnum
from ..schemas.resources import ResourceActionRequest
from ..schemas.workflow import WorkflowConfig
from .decision_evidence import PolicyEvidence
from .policy_rules import (
    BasePolicyRule,
    HighRiskOperationRule,
    MalformedRequestRule,
    PeerCommunicationRule,
    ProvenanceIntegrityRule,
    ResourceAuthorizationRule,
)
from .runtime_guardian import RuntimeGuardian


class PolicyEngine:
    """The authoritative policy enforcement engine for TRSM."""

    def __init__(
        self,
        guardian: Optional[RuntimeGuardian] = None,
        rules: Optional[List[BasePolicyRule]] = None,
    ):
        self.guardian = guardian or RuntimeGuardian()
        self.rules = rules or [
            MalformedRequestRule(),
            PeerCommunicationRule(),
            HighRiskOperationRule(),
            ResourceAuthorizationRule(),
            ProvenanceIntegrityRule(),
        ]
        self.policy_version = "1.0.0"

    def evaluate_message(
        self,
        proposal: AgentMessageProposal,
        workflow: Optional[WorkflowConfig] = None,
    ) -> PolicyDecision:
        """Evaluate an inter-agent message proposal through rules and threat detectors."""
        evaluated_rule_ids: List[str] = []
        evidence = PolicyEvidence(context_summary={"sender": proposal.sender_id, "recipient": proposal.recipient_id})

        # 1. Evaluate declarative rules
        for rule in self.rules:
            evaluated_rule_ids.append(rule.rule_id)
            res = rule.evaluate_message(proposal, workflow)
            evidence.rule_results.append(res)

            if not res.passed:
                evidence.matched_rule_ids.append(rule.rule_id)
                # Malformed or authorization failure immediately blocks
                return PolicyDecision(
                    request_id=proposal.proposal_id,
                    outcome=PolicyDecisionEnum.BLOCK,
                    reason_code=res.reason_code,
                    evidence=evidence.model_dump(),
                    applicable_rule_ids=evaluated_rule_ids,
                    policy_version=self.policy_version,
                )

        # 2. Scan with Runtime Guardian for prompt injection, memory poisoning, role hijacking
        findings = self.guardian.scan_message(proposal)
        evidence.threat_findings = findings

        if findings:
            top_finding = findings[0]
            evidence.risk_score = top_finding.confidence
            return PolicyDecision(
                request_id=proposal.proposal_id,
                outcome=top_finding.recommended_action,
                reason_code=f"THREAT_{top_finding.threat_family.value.upper()}",
                evidence=evidence.model_dump(),
                applicable_rule_ids=evaluated_rule_ids,
                policy_version=self.policy_version,
            )

        # 3. All checks passed -> ALLOW
        return PolicyDecision(
            request_id=proposal.proposal_id,
            outcome=PolicyDecisionEnum.ALLOW,
            reason_code="AUTHORIZED_PEER_COMMUNICATION",
            evidence=evidence.model_dump(),
            applicable_rule_ids=evaluated_rule_ids,
            policy_version=self.policy_version,
        )

    def evaluate_resource_action(
        self,
        action: ResourceActionRequest,
        workflow: Optional[WorkflowConfig] = None,
    ) -> PolicyDecision:
        """Evaluate a controlled resource action request."""
        evaluated_rule_ids: List[str] = []
        evidence = PolicyEvidence(
            context_summary={"requester": action.requester_id, "resource": action.resource_name, "op": action.operation}
        )

        # 1. Evaluate declarative rules
        for rule in self.rules:
            evaluated_rule_ids.append(rule.rule_id)
            res = rule.evaluate_resource_action(action, workflow)
            evidence.rule_results.append(res)

            if not res.passed:
                evidence.matched_rule_ids.append(rule.rule_id)
                # Check if high-risk rule triggered human-in-the-loop review
                if res.reason_code == "HIGH_RISK_OPERATION_REQUIRES_REVIEW":
                    return PolicyDecision(
                        request_id=action.action_id,
                        outcome=PolicyDecisionEnum.REVIEW,
                        reason_code=res.reason_code,
                        evidence=evidence.model_dump(),
                        applicable_rule_ids=evaluated_rule_ids,
                        policy_version=self.policy_version,
                    )

                return PolicyDecision(
                    request_id=action.action_id,
                    outcome=PolicyDecisionEnum.BLOCK,
                    reason_code=res.reason_code,
                    evidence=evidence.model_dump(),
                    applicable_rule_ids=evaluated_rule_ids,
                    policy_version=self.policy_version,
                )

        # 2. Scan with Runtime Guardian for memory poisoning / argument injection
        findings = self.guardian.scan_resource_action(action)
        evidence.threat_findings = findings

        if findings:
            top_finding = findings[0]
            evidence.risk_score = top_finding.confidence
            return PolicyDecision(
                request_id=action.action_id,
                outcome=top_finding.recommended_action,
                reason_code=f"THREAT_{top_finding.threat_family.value.upper()}",
                evidence=evidence.model_dump(),
                applicable_rule_ids=evaluated_rule_ids,
                policy_version=self.policy_version,
            )

        # 3. Authorized -> ALLOW
        return PolicyDecision(
            request_id=action.action_id,
            outcome=PolicyDecisionEnum.ALLOW,
            reason_code="AUTHORIZED_RESOURCE_OPERATION",
            evidence=evidence.model_dump(),
            applicable_rule_ids=evaluated_rule_ids,
            policy_version=self.policy_version,
        )
