"""Declarative, configurable policy rules for TRSM."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..schemas.messages import AgentMessageProposal
from ..schemas.provenance import TrustLabel
from ..schemas.resources import ResourceActionRequest, ResourceActionType
from ..schemas.workflow import WorkflowConfig
from .decision_evidence import RuleEvaluationResult


class BasePolicyRule(ABC):
    """Abstract base class for all declarative policy rules."""
    rule_id: str
    rule_name: str

    @abstractmethod
    def evaluate_message(
        self, proposal: AgentMessageProposal, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        """Evaluate rule against an inter-agent message proposal."""
        pass

    @abstractmethod
    def evaluate_resource_action(
        self, action: ResourceActionRequest, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        """Evaluate rule against a controlled resource request."""
        pass


class MalformedRequestRule(BasePolicyRule):
    """Ensures proposals and requests are structurally valid and contain required fields."""
    rule_id = "RULE-001"
    rule_name = "MalformedRequestValidation"

    def evaluate_message(
        self, proposal: AgentMessageProposal, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        if not proposal.sender_id or not proposal.sender_id.strip():
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="MALFORMED_SENDER_ID",
                details={"error": "Sender ID cannot be empty"},
            )
        if not proposal.recipient_id or not proposal.recipient_id.strip():
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="MALFORMED_RECIPIENT_ID",
                details={"error": "Recipient ID cannot be empty"},
            )
        if proposal.sender_id == proposal.recipient_id:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="SELF_COMMUNICATION_DISALLOWED",
                details={"error": "Agent cannot send message to itself"},
            )
        return RuleEvaluationResult(
            rule_id=self.rule_id, rule_name=self.rule_name, passed=True, reason_code="OK"
        )

    def evaluate_resource_action(
        self, action: ResourceActionRequest, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        if not action.requester_id or not action.requester_id.strip():
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="MALFORMED_REQUESTER_ID",
                details={"error": "Requester ID cannot be empty"},
            )
        if not action.resource_name or not action.resource_name.strip():
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="MALFORMED_RESOURCE_NAME",
                details={"error": "Resource name cannot be empty"},
            )
        return RuleEvaluationResult(
            rule_id=self.rule_id, rule_name=self.rule_name, passed=True, reason_code="OK"
        )


class PeerCommunicationRule(BasePolicyRule):
    """Enforces role-scoped peer communication allowlists."""
    rule_id = "RULE-002"
    rule_name = "PeerCommunicationAuthorization"

    def evaluate_message(
        self, proposal: AgentMessageProposal, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        if not workflow:
            # Without workflow context, fail closed on unverified peers
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="NO_WORKFLOW_CONTEXT",
                details={"error": "Workflow context required to verify peer permissions"},
            )

        sender_node = next((n for n in workflow.nodes if n.node_id == proposal.sender_id), None)
        if not sender_node:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="UNKNOWN_SENDER_NODE",
                details={"sender_id": proposal.sender_id},
            )

        recipient_node = next((n for n in workflow.nodes if n.node_id == proposal.recipient_id), None)
        if not recipient_node:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="UNKNOWN_RECIPIENT_NODE",
                details={"recipient_id": proposal.recipient_id},
            )

        if proposal.recipient_id not in sender_node.allowed_peers:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="PEER_NOT_ALLOWED",
                details={
                    "sender": proposal.sender_id,
                    "recipient": proposal.recipient_id,
                    "allowed_peers": sender_node.allowed_peers,
                },
            )

        return RuleEvaluationResult(
            rule_id=self.rule_id, rule_name=self.rule_name, passed=True, reason_code="OK"
        )

    def evaluate_resource_action(
        self, action: ResourceActionRequest, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        return RuleEvaluationResult(
            rule_id=self.rule_id, rule_name=self.rule_name, passed=True, reason_code="NOT_APPLICABLE"
        )


class ResourceAuthorizationRule(BasePolicyRule):
    """Enforces role-scoped tool, database, and memory access control."""
    rule_id = "RULE-003"
    rule_name = "ResourceRoleAuthorization"

    # Strict operation permissions by resource and role
    ROLE_PERMISSIONS: Dict[str, Dict[str, List[str]]] = {
        "customer_db": {
            "backend": ["read_profile"],
            "db_manager": ["read_profile", "write_profile"],
            "qa": ["read_profile"],
            "devops": [],
        },
        "test_suite": {
            "qa": ["run_tests", "get_results"],
            "backend": ["get_results"],
            "devops": ["get_results"],
            "db_manager": [],
        },
        "deployment_manager": {
            "devops": ["deploy_staging", "deploy_production"],
            "backend": [],
            "db_manager": [],
            "qa": [],
        },
        "workflow_memory": {
            "backend": ["read"],
            "db_manager": ["read", "write"],
            "qa": ["read"],
            "devops": ["read"],
        },
    }

    def evaluate_message(
        self, proposal: AgentMessageProposal, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        return RuleEvaluationResult(
            rule_id=self.rule_id, rule_name=self.rule_name, passed=True, reason_code="NOT_APPLICABLE"
        )

    def evaluate_resource_action(
        self, action: ResourceActionRequest, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        if not workflow:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="NO_WORKFLOW_CONTEXT",
                details={"error": "Workflow context required to verify resource permissions"},
            )

        requester = next((n for n in workflow.nodes if n.node_id == action.requester_id), None)
        if not requester:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="UNKNOWN_REQUESTER",
                details={"requester_id": action.requester_id},
            )

        # 1. Check if tool is assigned to the agent configuration
        if action.resource_name not in requester.allowed_tools:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="TOOL_NOT_ASSIGNED_TO_NODE",
                details={
                    "requester": action.requester_id,
                    "resource": action.resource_name,
                    "allowed_tools": requester.allowed_tools,
                },
            )

        # 2. Check role capability matrix
        role_str = requester.role.value
        resource_rules = self.ROLE_PERMISSIONS.get(action.resource_name)
        if not resource_rules:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="UNREGISTERED_RESOURCE",
                details={"resource": action.resource_name},
            )

        allowed_ops = resource_rules.get(role_str, [])
        if action.operation not in allowed_ops:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="OPERATION_FORBIDDEN_FOR_ROLE",
                details={
                    "role": role_str,
                    "resource": action.resource_name,
                    "operation": action.operation,
                    "allowed_operations": allowed_ops,
                },
            )

        return RuleEvaluationResult(
            rule_id=self.rule_id, rule_name=self.rule_name, passed=True, reason_code="OK"
        )


class HighRiskOperationRule(BasePolicyRule):
    """Flags high-impact or destructive operations that require Human-in-the-Loop REVIEW."""
    rule_id = "RULE-004"
    rule_name = "HighRiskOperationReview"

    HIGH_RISK_OPERATIONS = {
        ("deployment_manager", "deploy_production"),
        ("customer_db", "drop_table"),
        ("customer_db", "delete_all"),
    }

    def evaluate_message(
        self, proposal: AgentMessageProposal, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        return RuleEvaluationResult(
            rule_id=self.rule_id, rule_name=self.rule_name, passed=True, reason_code="NOT_APPLICABLE"
        )

    def evaluate_resource_action(
        self, action: ResourceActionRequest, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        key = (action.resource_name, action.operation)
        if key in self.HIGH_RISK_OPERATIONS:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                passed=False,
                reason_code="HIGH_RISK_OPERATION_REQUIRES_REVIEW",
                details={
                    "resource": action.resource_name,
                    "operation": action.operation,
                    "requires_review": True,
                },
            )
        return RuleEvaluationResult(
            rule_id=self.rule_id, rule_name=self.rule_name, passed=True, reason_code="OK"
        )


class ProvenanceIntegrityRule(BasePolicyRule):
    """Enforces that untrusted external inputs cannot directly invoke privileged write actions."""
    rule_id = "RULE-005"
    rule_name = "ProvenanceIntegrityControl"

    def evaluate_message(
        self, proposal: AgentMessageProposal, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        return RuleEvaluationResult(
            rule_id=self.rule_id, rule_name=self.rule_name, passed=True, reason_code="NOT_APPLICABLE"
        )

    def evaluate_resource_action(
        self, action: ResourceActionRequest, workflow: Optional[WorkflowConfig]
    ) -> RuleEvaluationResult:
        if action.provenance:
            # If provenance contains UNTRUSTED_EXTERNAL and lacks VALIDATED
            labels = action.provenance.trust_labels
            if TrustLabel.UNTRUSTED_EXTERNAL in labels and TrustLabel.VALIDATED not in labels:
                if action.action_type in [ResourceActionType.DB_WRITE, ResourceActionType.MEMORY_WRITE]:
                    return RuleEvaluationResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        passed=False,
                        reason_code="UNVALIDATED_EXTERNAL_DATA_WRITE_BLOCKED",
                        details={
                            "labels": [l.value for l in labels],
                            "action_type": action.action_type.value,
                        },
                    )
        return RuleEvaluationResult(
            rule_id=self.rule_id, rule_name=self.rule_name, passed=True, reason_code="OK"
        )
