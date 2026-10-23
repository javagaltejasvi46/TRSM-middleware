"""Prompt injection detection heuristics and pattern analysis."""

import re
from typing import List, Optional
from ...schemas.threats import ThreatFamily, ThreatFinding, ThreatSeverity

# Categorized prompt injection regex patterns
INJECTION_PATTERNS = [
    # Direct instruction override
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", "Direct instruction override attempt", ThreatSeverity.HIGH, 0.95),
    (r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions", "Direct instruction override attempt", ThreatSeverity.HIGH, 0.95),
    (r"system\s+prompt\s+override", "Explicit system prompt override", ThreatSeverity.HIGH, 0.92),
    # Exfiltration of credentials
    (r"dump\s+(all\s+)?(passwords|credentials|database|tokens|secrets|keys)", "Credential exfiltration attempt", ThreatSeverity.CRITICAL, 0.96),
    (r"print\s+(the\s+)?(system\s+prompt|initial\s+prompt|hidden\s+instructions)", "System prompt exfiltration attempt", ThreatSeverity.HIGH, 0.90),
    # Jailbreak / Developer mode
    (r"you\s+are\s+now\s+in\s+developer\s+mode", "Developer mode jailbreak attempt", ThreatSeverity.HIGH, 0.91),
    (r"dan\s+mode\s+enabled", "DAN jailbreak signature", ThreatSeverity.HIGH, 0.93),
    (r"bypass\s+(all\s+)?(security|guardrails|filters|policy)", "Guardrail bypass attempt", ThreatSeverity.CRITICAL, 0.97),
    # Propagated hidden instructions in external content
    (r"\[system\s+alert:.*?forward\s+command", "Propagated external injection marker", ThreatSeverity.CRITICAL, 0.94),
    (r"hidden\s+instruction:\s*['\"].*?['\"]", "Hidden payload injection", ThreatSeverity.HIGH, 0.90),
]


class PromptInjectionDetector:
    """Detects prompt injection and instruction overrides in message contents."""

    def detect(self, text: str, source_event_id: str) -> List[ThreatFinding]:
        findings: List[ThreatFinding] = []
        lower_text = text.lower()

        for pattern, description, severity, confidence in INJECTION_PATTERNS:
            match = re.search(pattern, lower_text)
            if match:
                findings.append(
                    ThreatFinding(
                        threat_family=ThreatFamily.PROMPT_INJECTION,
                        severity=severity,
                        confidence=confidence,
                        source_event_id=source_event_id,
                        evidence_summary=f"{description}: '{match.group(0)}'",
                        raw_evidence={"matched_pattern": pattern, "matched_text": match.group(0)},
                    )
                )

        return findings
