"""Authoritative TRSM Policy Enforcement Engine."""

from typing import Dict, List, Optional
from ..schemas.messages import AgentMessageProposal
from ..schemas.policy import PolicyDecision, PolicyDecisionEnum
from ..schemas.resources import ResourceActionRequest
from ..schemas.workflow import WorkflowConfig
from .runtime_guardian import RuntimeGuardian


class PolicyEngine:
    """The central authority for ALLOW, BLOCK, QUARANTINE, and REVIEW decisions."""

    def __init__(self, guardian: Optional[RuntimeGuardian] = None):
        self.guardian = guardian or RuntimeGuardian()
        self.policy_version = "1.0.0"

    def evaluate_message(
        self,
        proposal: AgentMessageProposal,
        workflow: Optional[WorkflowConfig] = None,
    ) -> PolicyDecision:
        """Evaluate an inter-agent message proposal."""
        # 1. Structural check: unknown sender or recipient
        if not proposal.sender_id or not proposal.recipient_id:
            return PolicyDecision(
                request_id=proposal.proposal_id,
                outcome=PolicyDecisionEnum.BLOCK,
                reason_code="MALFORMED_PROPOSAL",
                evidence={"error": "Sender and recipient IDs must be non-empty."},
                policy_version=self.policy_version,
            )

        # 2. Check workflow configuration permissions if provided
        if workflow:
            sender_node = next((n for n in workflow.nodes if n.node_id == proposal.sender_id), None)
            if not sender_node:
                return PolicyDecision(
                    request_id=proposal.proposal_id,
                    outcome=PolicyDecisionEnum.BLOCK,
                    reason_code="UNKNOWN_SENDER",
                    evidence={"sender_id": proposal.sender_id},
                    policy_version=self.policy_version,
                )

            # Check peer permission
            if proposal.recipient_id not in sender_node.allowed_peers:
                return PolicyDecision(
                    request_id=proposal.proposal_id,
                    outcome=PolicyDecisionEnum.BLOCK,
                    reason_code="PEER_NOT_ALLOWED",
                    evidence={
                        "sender": proposal.sender_id,
                        "recipient": proposal.recipient_id,
                        "allowed_peers": sender_node.allowed_peers,
                    },
                    policy_version=self.policy_version,
                )

        # 3. Check with Runtime Guardian for prompt injection or role hijacking
        findings = self.guardian.scan_message(proposal)
        if findings:
            top_finding = findings[0]
            return PolicyDecision(
                request_id=proposal.proposal_id,
                outcome=top_finding.recommended_action,
                reason_code=f"THREAT_{top_finding.threat_family.upper()}",
                evidence={
                    "finding_id": top_finding.finding_id,
                    "threat_family": top_finding.threat_family,
                    "summary": top_finding.evidence_summary,
                },
                policy_version=self.policy_version,
            )

        return PolicyDecision(
            request_id=proposal.proposal_id,
            outcome=PolicyDecisionEnum.ALLOW,
            reason_code="AUTHORIZED_PEER_COMMUNICATION",
            policy_version=self.policy_version,
        )

    def evaluate_resource_action(
        self,
        action: ResourceActionRequest,
        workflow: Optional[WorkflowConfig] = None,
    ) -> PolicyDecision:
        """Evaluate an agent's request to use a tool, query DB, or modify memory."""
        # Check node permissions if workflow provided
        if workflow:
            requester_node = next((n for n in workflow.nodes if n.node_id == action.requester_id), None)
            if not requester_node:
                return PolicyDecision(
                    request_id=action.action_id,
                    outcome=PolicyDecisionEnum.BLOCK,
                    reason_code="UNKNOWN_REQUESTER",
                    evidence={"requester_id": action.requester_id},
                    policy_version=self.policy_version,
                )

            if action.resource_name not in requester_node.allowed_tools:
                return PolicyDecision(
                    request_id=action.action_id,
                    outcome=PolicyDecisionEnum.BLOCK,
                    reason_code="RESOURCE_NOT_ALLOWED",
                    evidence={
                        "requester": action.requester_id,
                        "resource": action.resource_name,
                        "allowed_tools": requester_node.allowed_tools,
                    },
                    policy_version=self.policy_version,
                )

        # Check with Runtime Guardian for memory poisoning or command injection
        findings = self.guardian.scan_resource_action(action)
        if findings:
            top_finding = findings[0]
            return PolicyDecision(
                request_id=action.action_id,
                outcome=top_finding.recommended_action,
                reason_code=f"THREAT_{top_finding.threat_family.upper()}",
                evidence={
                    "finding_id": top_finding.finding_id,
                    "threat_family": top_finding.threat_family,
                    "summary": top_finding.evidence_summary,
                },
                policy_version=self.policy_version,
            )

        return PolicyDecision(
            request_id=action.action_id,
            outcome=PolicyDecisionEnum.ALLOW,
            reason_code="AUTHORIZED_RESOURCE_OPERATION",
            policy_version=self.policy_version,
        )
