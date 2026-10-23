"""Role and orchestrator hijacking detection heuristics."""

import re
from typing import List
from ...schemas.threats import ThreatFamily, ThreatFinding, ThreatSeverity

ROLE_HIJACKING_PATTERNS = [
    (r"assume\s+role\s+['\"]?(devops_admin|admin|root|superuser|orchestrator)", "Attempted unauthorized role escalation", ThreatSeverity.CRITICAL, 0.98),
    (r"you\s+are\s+now\s+the\s+(orchestrator|master|system)", "Orchestrator persona hijacking attempt", ThreatSeverity.CRITICAL, 0.96),
    (r"escalate\s+(privileges\s+to\s+)?(root|admin|devops)", "Privilege escalation attempt", ThreatSeverity.CRITICAL, 0.97),
    (r"masquerade\s+as\s+['\"]?[a-zA-Z0-9_]+['\"]?", "Identity masquerade directive", ThreatSeverity.HIGH, 0.92),
    (r"switch\s+identity\s+to\s+['\"]?[a-zA-Z0-9_]+['\"]?", "Identity spoofing directive", ThreatSeverity.HIGH, 0.91),
]


class RoleHijackingDetector:
    """Detects unauthorized role assumption, masquerading, or orchestrator override attempts."""

    def detect(self, text: str, source_event_id: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []
        lower_text = text.lower()

        for pattern, description, severity, confidence in ROLE_HIJACKING_PATTERNS:
            match = re.search(pattern, lower_text)
            if match:
                findings.append(
                    ThreatFinding(
                        threat_family=ThreatFamily.ROLE_HIJACKING,
                        severity=severity,
                        confidence=confidence,
                        source_event_id=source_event_id,
                        evidence_summary=f"{description}: '{match.group(0)}'",
                        raw_evidence={"matched_pattern": pattern, "matched_text": match.group(0)},
                    )
                )

        return findings
