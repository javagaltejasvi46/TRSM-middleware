"""Prompt injection detection heuristics."""

import re
from typing import List, Optional
from ...schemas.threats import ThreatFamily, ThreatFinding, ThreatSeverity

PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+prompt\s+override",
    r"dump\s+(all\s+)?(passwords|credentials|database|tokens)",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"bypass\s+(all\s+)?(security|guardrails|filters)",
]


class PromptInjectionDetector:
    """Detects prompt injection and instruction overrides in message contents."""

    def detect(self, text: str, source_event_id: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []
        lower_text = text.lower()

        for pattern in PATTERNS:
            match = re.search(pattern, lower_text)
            if match:
                findings.append(
                    ThreatFinding(
                        threat_family=ThreatFamily.PROMPT_INJECTION,
                        severity=ThreatSeverity.HIGH,
                        confidence=0.92,
                        source_event_id=source_event_id,
                        evidence_summary=f"Matched known instruction override pattern: '{match.group(0)}'",
                        raw_evidence={"matched_pattern": pattern, "matched_text": match.group(0)},
                    )
                )
        return findings
