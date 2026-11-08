from fastapi import APIRouter, HTTPException, status
from typing import List, Dict
from backend.app.contracts.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowDefinition
)
from backend.app.runtime.validator import validate_workflow_definition

router = APIRouter()

# In-memory store (will be backed by SQLite in Phase 6)
_WORKFLOWS: Dict[str, WorkflowResponse] = {}

@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(payload: WorkflowCreate):
    errors = validate_workflow_definition(payload.definition)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors}
        )

    wf_id = f"wf-{len(_WORKFLOWS) + 1}"
    wf = WorkflowResponse(id=wf_id, name=payload.name, definition=payload.definition)
    _WORKFLOWS[wf_id] = wf
    return wf

@router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows():
    return list(_WORKFLOWS.values())

@router.get("/workflows/{wf_id}", response_model=WorkflowResponse)
async def get_workflow(wf_id: str):
    wf = _WORKFLOWS.get(wf_id)
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return wf

@router.put("/workflows/{wf_id}", response_model=WorkflowResponse)
async def update_workflow(wf_id: str, payload: WorkflowUpdate):
    wf = _WORKFLOWS.get(wf_id)
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    new_name = payload.name if payload.name is not None else wf.name
    new_def = payload.definition if payload.definition is not None else wf.definition

    if payload.definition is not None:
        errors = validate_workflow_definition(new_def)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"errors": errors}
            )

    updated_wf = WorkflowResponse(id=wf_id, name=new_name, definition=new_def)
    _WORKFLOWS[wf_id] = updated_wf
    return updated_wf

@router.post("/workflows/validate")
async def validate_workflow(definition: WorkflowDefinition):
    """
    Dedicated endpoint to validate workflow JSON without creating/saving it.
    """
    errors = validate_workflow_definition(definition)
    if errors:
        return {"valid": False, "errors": errors}
    return {"valid": True, "errors": []}
