"""Workflow configuration and validation API routes backed by SQLite."""

from typing import List
from fastapi import APIRouter, HTTPException, status

from ...persistence.workflow_repository import WorkflowRepository
from ...runtime.graph_validator import GraphValidator
from ...schemas.workflow import WorkflowConfig, WorkflowValidationResult

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


@router.post("/validate", response_model=WorkflowValidationResult)
async def validate_workflow(workflow: WorkflowConfig):
    """Validate graph structure, node connections, and permission consistency."""
    validator = GraphValidator()
    return validator.validate(workflow)


@router.post("", response_model=WorkflowConfig, status_code=status.HTTP_201_CREATED)
async def create_workflow(workflow: WorkflowConfig):
    """Save a validated workflow configuration to SQLite."""
    validator = GraphValidator()
    validation = validator.validate(workflow)
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Invalid workflow configuration", "errors": validation.errors},
        )
    repo = WorkflowRepository()
    return await repo.save(workflow)


@router.get("", response_model=List[WorkflowConfig])
async def list_workflows():
    """List all saved workflows from SQLite."""
    repo = WorkflowRepository()
    return await repo.list_all()


@router.get("/{workflow_id}", response_model=WorkflowConfig)
async def get_workflow(workflow_id: str):
    """Retrieve a specific workflow by ID."""
    repo = WorkflowRepository()
    wf = await repo.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return wf


@router.put("/{workflow_id}", response_model=WorkflowConfig)
async def update_workflow(workflow_id: str, workflow: WorkflowConfig):
    """Update an existing workflow configuration."""
    if workflow.workflow_id != workflow_id:
        workflow.workflow_id = workflow_id
    validator = GraphValidator()
    validation = validator.validate(workflow)
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Invalid workflow configuration", "errors": validation.errors},
        )
    repo = WorkflowRepository()
    return await repo.save(workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str):
    """Delete a workflow configuration by ID."""
    repo = WorkflowRepository()
    deleted = await repo.delete(workflow_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return None
