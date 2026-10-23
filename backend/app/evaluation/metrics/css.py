"""Component Synergy Score (CSS) calculation logic."""

from typing import List
from ...schemas.events import AuditEvent, AuditEventType
from ...schemas.metrics import MetricResult


class CSSCalculator:
    """Calculates Component Synergy Score based on communication and delivery ratio."""

    def calculate(self, events: List[AuditEvent]) -> MetricResult:
        proposed_msgs = [e for e in events if e.event_type == AuditEventType.MESSAGE_PROPOSED]
        delivered_msgs = [e for e in events if e.event_type == AuditEventType.MESSAGE_DELIVERED]

        total_proposed = len(proposed_msgs)
        total_delivered = len(delivered_msgs)

        if total_proposed == 0:
            return MetricResult(
                name="Component Synergy Score (CSS)",
                value=1.0,
                available=True,
                numerator=0.0,
                denominator=0.0,
                metadata={"note": "No inter-agent messages proposed in run"},
            )

        # Baseline synergy calculation: ratio of successful coordinated deliveries without cycles
        synergy_score = round(total_delivered / total_proposed, 4)

        return MetricResult(
            name="Component Synergy Score (CSS)",
            value=synergy_score,
            available=True,
            numerator=float(total_delivered),
            denominator=float(total_proposed),
            metadata={"total_proposed": total_proposed, "total_delivered": total_delivered},
        )
