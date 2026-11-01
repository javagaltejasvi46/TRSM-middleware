from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Any

router = APIRouter()

class WorkflowCreate(BaseModel):
    name: str = Field(..., description="Human‑readable workflow name")
    definition: Any = Field(..., description="Raw workflow JSON definition")

class WorkflowResponse(BaseModel):
    id: str
    name: str
    definition: Any

# In‑memory placeholder store (will be replaced by DB later)
_WORKFLOWS: dict[str, WorkflowResponse] = {}

@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(payload: WorkflowCreate):
    # generate a simple deterministic id for now
    wf_id = f"wf-{len(_WORKFLOWS)+1}"
    wf = WorkflowResponse(id=wf_id, name=payload.name, definition=payload.definition)
    _WORKFLOWS[wf_id] = wf
    return wf

@router.get("/workflows/{wf_id}", response_model=WorkflowResponse)
async def get_workflow(wf_id: str):
    wf = _WORKFLOWS.get(wf_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf

