from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any

router = APIRouter()

class Event(BaseModel):
    event_id: str
    run_id: str
    event_type: str
    timestamp: str
    payload: Dict[str, Any] = Field(default_factory=dict)

# In‑memory placeholder store
_EVENTS: List[Event] = []

@router.get("/events", response_model=List[Event])
async def list_events(run_id: str | None = None):
    if run_id:
        return [e for e in _EVENTS if e.run_id == run_id]
    return _EVENTS

@router.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    for e in _EVENTS:
        if e.event_id == event_id:
            return e
    raise HTTPException(status_code=404, detail="Event not found")

