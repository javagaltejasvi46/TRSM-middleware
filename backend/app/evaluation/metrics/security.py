"""Security evaluation metrics: ASR, FPR, and FNR."""

from typing import Any, Dict, List
from ...schemas.metrics import MetricResult


class SecurityMetricsCalculator:
    """Calculates Attack Success Rate (ASR), False Positive Rate (FPR), and False Negative Rate (FNR)."""

    def calculate_asr(self, total_attacks: int, successful_attacks: int) -> MetricResult:
        """Attack Success Rate (ASR) = successful attacks / total attack trials."""
        if total_attacks == 0:
            return MetricResult(
                name="Attack Success Rate (ASR)",
                value=None,
                available=False,
                unavailable_reason="No adversarial attack trials executed in dataset.",
                numerator=0.0,
                denominator=0.0,
            )

        asr = round(successful_attacks / total_attacks, 4)
        return MetricResult(
            name="Attack Success Rate (ASR)",
            value=asr,
            available=True,
            numerator=float(successful_attacks),
            denominator=float(total_attacks),
            metadata={"successful_attacks": successful_attacks, "total_attacks": total_attacks},
        )

    def calculate_fpr(self, total_benign: int, false_blocks: int) -> MetricResult:
        """False Positive Rate (FPR) = benign actions blocked / total legitimate benign actions."""
        if total_benign == 0:
            return MetricResult(
                name="False Positive Rate (FPR)",
                value=None,
                available=False,
                unavailable_reason="No legitimate benign actions executed in dataset.",
                numerator=0.0,
                denominator=0.0,
            )

        fpr = round(false_blocks / total_benign, 4)
        return MetricResult(
            name="False Positive Rate (FPR)",
            value=fpr,
            available=True,
            numerator=float(false_blocks),
            denominator=float(total_benign),
            metadata={"false_blocks": false_blocks, "total_benign": total_benign},
        )

    def calculate_fnr(self, total_adversarial: int, missed_attacks: int) -> MetricResult:
        """False Negative Rate (FNR) = adversarial actions allowed / total adversarial actions."""
        if total_adversarial == 0:
            return MetricResult(
                name="False Negative Rate (FNR)",
                value=None,
                available=False,
                unavailable_reason="No adversarial actions evaluated in dataset.",
                numerator=0.0,
                denominator=0.0,
            )

        fnr = round(missed_attacks / total_adversarial, 4)
        return MetricResult(
            name="False Negative Rate (FNR)",
            value=fnr,
            available=True,
            numerator=float(missed_attacks),
            denominator=float(total_adversarial),
            metadata={"missed_attacks": missed_attacks, "total_adversarial": total_adversarial},
        )
