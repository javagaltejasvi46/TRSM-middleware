"""Audit events API routes."""

from typing import List, Optional
from fastapi import APIRouter, Query

from ...schemas.events import AuditEvent
from ...services.trace_service import TraceService

router = APIRouter(prefix="/api/runs/{run_id}", tags=["Audit & Traces"])


@router.get("/events", response_model=List[AuditEvent])
async def get_run_events(
    run_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    actor_id: Optional[str] = Query(None, description="Filter by actor node ID"),
):
    """Retrieve structured audit events for a specific run."""
    trace_service = TraceService()
    return await trace_service.get_events(run_id=run_id, event_type=event_type, actor_id=actor_id)


@router.get("/trace")
async def get_run_trace(run_id: str):
    """Reconstruct causal execution trace graph for frontend explorer."""
    trace_service = TraceService()
    return await trace_service.get_trace_graph(run_id=run_id)
