"""Tool Utilization Efficacy (TUE) calculation logic."""

from typing import List
from ...schemas.events import AuditEvent, AuditEventType
from ...schemas.metrics import MetricResult


class TUECalculator:
    """Calculates Tool Utilization Efficacy based on authorized tool executions."""

    def calculate(self, events: List[AuditEvent]) -> MetricResult:
        proposed_tools = [e for e in events if e.event_type == AuditEventType.RESOURCE_PROPOSED]
        executed_tools = [e for e in events if e.event_type == AuditEventType.RESOURCE_EXECUTED]

        total_proposed = len(proposed_tools)
        total_executed = len(executed_tools)

        if total_proposed == 0:
            return MetricResult(
                name="Tool Utilization Efficacy (TUE)",
                value=1.0,
                available=True,
                numerator=0.0,
                denominator=0.0,
                metadata={"note": "No tools proposed in run"},
            )

        tue_score = round(total_executed / total_proposed, 4)

        return MetricResult(
            name="Tool Utilization Efficacy (TUE)",
            value=tue_score,
            available=True,
            numerator=float(total_executed),
            denominator=float(total_proposed),
            metadata={"total_proposed": total_proposed, "total_executed": total_executed},
        )
