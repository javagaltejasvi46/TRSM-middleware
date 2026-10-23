"""Memory poisoning detection heuristics."""

import re
from typing import Any, Dict, List
from ...schemas.threats import ThreatFamily, ThreatFinding, ThreatSeverity

MEMORY_POISONING_PATTERNS = [
    (r"bypass\s+manual\s+audit", "Instruction to bypass audit verification", ThreatSeverity.CRITICAL, 0.96),
    (r"elevate\s+privileges", "Unauthorized privilege escalation directive", ThreatSeverity.CRITICAL, 0.95),
    (r"disable\s+(logging|telemetry|audit)", "Directive to suppress audit stream", ThreatSeverity.CRITICAL, 0.97),
    (r"always\s+(approve|allow)", "Adversarial policy rewrite directive", ThreatSeverity.HIGH, 0.92),
    (r"overwrite\s+system\s+(policy|prompt)", "System policy override directive", ThreatSeverity.CRITICAL, 0.98),
]

FORBIDDEN_MEMORY_KEYS = {
    "system_policy",
    "root_config",
    "security_rules",
    "auth_tokens",
    "master_key",
}


class MemoryPoisoningDetector:
    """Detects attempts to write adversarial policy instructions or overwrite protected memory keys."""

    def detect(self, key: str, value: Any, source_event_id: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []
        lower_key = str(key).lower().strip()
        text_val = str(value).lower()

        # Check protected key override
        if lower_key in FORBIDDEN_MEMORY_KEYS:
            findings.append(
                ThreatFinding(
                    threat_family=ThreatFamily.MEMORY_POISONING,
                    severity=ThreatSeverity.CRITICAL,
                    confidence=0.99,
                    source_event_id=source_event_id,
                    evidence_summary=f"Attempted write to protected system memory key: '{key}'",
                    raw_evidence={"protected_key": key},
                )
            )

        # Check suspicious payload patterns
        for pattern, description, severity, confidence in MEMORY_POISONING_PATTERNS:
            match = re.search(pattern, text_val)
            if match:
                findings.append(
                    ThreatFinding(
                        threat_family=ThreatFamily.MEMORY_POISONING,
                        severity=severity,
                        confidence=confidence,
                        source_event_id=source_event_id,
                        evidence_summary=f"Memory write contains override attempt: '{match.group(0)}'",
                        raw_evidence={"key": key, "matched_pattern": pattern, "description": description},
                    )
                )

        return findings
