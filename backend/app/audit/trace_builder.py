"""Causal trace DAG reconstructor."""

from typing import Any, Dict, List
from ..schemas.events import AuditEvent


class TraceBuilder:
    """Builds a connected execution DAG from audit events."""

    def build_trace_graph(self, events: List[AuditEvent]) -> Dict[str, Any]:
        nodes = []
        links = []

        for evt in events:
            nodes.append({
                "id": evt.event_id,
                "label": evt.event_type.value,
                "actor": evt.actor_id,
                "target": evt.target_id,
                "decision": evt.policy_decision.value if evt.policy_decision else None,
                "reason_code": evt.reason_code,
                "timestamp": evt.timestamp.isoformat(),
            })
            if evt.parent_event_id:
                links.append({
                    "source": evt.parent_event_id,
                    "target": evt.event_id,
                })

        return {
            "run_id": events[0].run_id if events else None,
            "total_events": len(events),
            "nodes": nodes,
            "links": links,
        }
