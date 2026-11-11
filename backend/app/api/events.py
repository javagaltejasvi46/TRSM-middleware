from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from backend.app.contracts.events import AuditEvent
from backend.app.persistence.event_repository import event_repository

router = APIRouter()

@router.get("/events", response_model=List[AuditEvent])
async def list_events(
    run_id: Optional[str] = Query(None, description="Filter events by run ID"),
    actor_id: Optional[str] = Query(None, description="Filter events by actor ID"),
    event_type: Optional[str] = Query(None, description="Filter events by event type"),
    policy_decision: Optional[str] = Query(None, description="Filter events by policy decision (ALLOW, BLOCK, etc.)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    return event_repository.list_events(
        run_id=run_id,
        actor_id=actor_id,
        event_type=event_type,
        policy_decision=policy_decision,
        limit=limit,
        offset=offset
    )

@router.get("/events/{event_id}", response_model=AuditEvent)
async def get_event(event_id: str):
    evt = event_repository.get_event(event_id)
    if not evt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' not found."
        )
    return evt
