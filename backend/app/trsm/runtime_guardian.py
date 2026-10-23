"""Runtime Guardian coordinating threat family detectors."""

from typing import List
from ..schemas.messages import AgentMessageProposal
from ..schemas.resources import ResourceActionRequest, ResourceActionType
from ..schemas.threats import ThreatFinding
from .detectors import (
    MemoryPoisoningDetector,
    PromptInjectionDetector,
    RoleHijackingDetector,
)


class RuntimeGuardian:
    """Coordinates detection across prompt injection, memory poisoning, and role hijacking."""

    def __init__(self):
        self.injection_detector = PromptInjectionDetector()
        self.memory_detector = MemoryPoisoningDetector()
        self.role_detector = RoleHijackingDetector()

    def scan_message(self, proposal: AgentMessageProposal) -> List[ThreatFinding]:
        """Scan inter-agent message content for threats."""
        findings: List[ThreatFinding] = []
        findings.extend(
            self.injection_detector.detect(proposal.content, source_event_id=proposal.proposal_id)
        )
        findings.extend(
            self.role_detector.detect(proposal.content, source_event_id=proposal.proposal_id)
        )
        return findings

    def scan_resource_action(self, action: ResourceActionRequest) -> List[ThreatFinding]:
        """Scan tool arguments or memory write operations for threats."""
        findings: List[ThreatFinding] = []
        if action.action_type == ResourceActionType.MEMORY_WRITE:
            key = action.arguments.get("key", "")
            val = action.arguments.get("value", "")
            findings.extend(
                self.memory_detector.detect(key, val, source_event_id=action.action_id)
            )
        return findings
