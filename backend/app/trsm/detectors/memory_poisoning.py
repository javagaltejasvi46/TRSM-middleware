"""Memory poisoning detection heuristics."""

import re
from typing import Any, Dict, List
from ...schemas.threats import ThreatFamily, ThreatFinding, ThreatSeverity

SUSPICIOUS_MEMORY_PATTERNS = [
    r"bypass\s+manual\s+audit",
    r"elevate\s+privileges",
    r"disable\s+logging",
    r"always\s+approve",
]


class MemoryPoisoningDetector:
    """Detects attempts to write adversarial policy instructions into shared memory."""

    def detect(self, key: str, value: Any, source_event_id: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []
        text_val = str(value).lower()

        for pattern in SUSPICIOUS_MEMORY_PATTERNS:
            match = re.search(pattern, text_val)
            if match:
                findings.append(
                    ThreatFinding(
                        threat_family=ThreatFamily.MEMORY_POISONING,
                        severity=ThreatSeverity.CRITICAL,
                        confidence=0.95,
                        source_event_id=source_event_id,
                        evidence_summary=f"Memory write contains override attempt: '{match.group(0)}'",
                        raw_evidence={"key": key, "matched_pattern": pattern},
                    )
                )
        return findings
