"""Application service for querying traces and events."""

from typing import Any, Dict, List, Optional
from ..audit.event_collector import AuditEventCollector
from ..audit.trace_builder import TraceBuilder
from ..schemas.events import AuditEvent


class TraceService:
    """Provides querying and graph assembly over stored audit records."""

    def __init__(self):
        self.collector = AuditEventCollector()
        self.trace_builder = TraceBuilder()

    async def get_events(
        self,
        run_id: str,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        policy_decision: Optional[str] = None,
    ) -> List[AuditEvent]:
        return await self.collector.get_events_for_run_async(
            run_id=run_id,
            event_type=event_type,
            actor_id=actor_id,
            policy_decision=policy_decision,
        )

    async def get_trace_graph(self, run_id: str) -> Dict[str, Any]:
        events = await self.collector.get_events_for_run_async(run_id=run_id)
        return self.trace_builder.build_trace_graph(events)
