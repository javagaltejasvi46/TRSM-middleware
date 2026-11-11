"""Workflow configuration and validation API routes."""

from typing import List
from fastapi import APIRouter, HTTPException, status

from ...schemas.workflow import WorkflowConfig, WorkflowValidationResult
from ...runtime.graph_validator import GraphValidator

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

# In-memory store for MVP fast prototyping (persisted through repository in milestone 1)
_WORKFLOWS_STORE = {}


@router.post("/validate", response_model=WorkflowValidationResult)
async def validate_workflow(workflow: WorkflowConfig):
    """Validate graph structure, node connections, and permission consistency."""
    validator = GraphValidator()
    return validator.validate(workflow)


@router.post("", response_model=WorkflowConfig, status_code=status.HTTP_201_CREATED)
async def create_workflow(workflow: WorkflowConfig):
    """Save a validated workflow configuration."""
    validator = GraphValidator()
    validation = validator.validate(workflow)
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Invalid workflow configuration", "errors": validation.errors}
        )
    _WORKFLOWS_STORE[workflow.workflow_id] = workflow
    return workflow


@router.get("", response_model=List[WorkflowConfig])
async def list_workflows():
    """List all saved workflows."""
    return list(_WORKFLOWS_STORE.values())


@router.get("/{workflow_id}", response_model=WorkflowConfig)
async def get_workflow(workflow_id: str):
    """Retrieve a specific workflow by ID."""
    if workflow_id not in _WORKFLOWS_STORE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return _WORKFLOWS_STORE[workflow_id]
