"""Role hijacking detection heuristics."""

import re
from typing import List
from ...schemas.threats import ThreatFamily, ThreatFinding, ThreatSeverity

HIJACK_PATTERNS = [
    r"assume\s+role\s+['\"]?devops",
    r"assume\s+role\s+['\"]?admin",
    r"you\s+are\s+now\s+the\s+orchestrator",
    r"escalate\s+to\s+root",
]


class RoleHijackingDetector:
    """Detects unauthorized role assumption or orchestrator override attempts."""

    def detect(self, text: str, source_event_id: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []
        lower_text = text.lower()

        for pattern in HIJACK_PATTERNS:
            match = re.search(pattern, lower_text)
            if match:
                findings.append(
                    ThreatFinding(
                        threat_family=ThreatFamily.ROLE_HIJACKING,
                        severity=ThreatSeverity.CRITICAL,
                        confidence=0.96,
                        source_event_id=source_event_id,
                        evidence_summary=f"Role escalation attempt detected: '{match.group(0)}'",
                        raw_evidence={"matched_pattern": pattern},
                    )
                )
        return findings
