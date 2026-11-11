"""Workflow configuration and validation API routes (Unified)."""

from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.app.contracts.workflow import (
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowResponse,
    WorkflowUpdate,
)
from backend.app.runtime.validator import validate_workflow_definition
from ..runtime.graph_validator import GraphValidator
from ..schemas.workflow import WorkflowConfig, WorkflowValidationResult

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

# Shared storage
_WORKFLOWS: Dict[str, WorkflowResponse] = {}
_WORKFLOWS_STORE: Dict[str, WorkflowConfig] = {}


@router.post("/validate")
async def validate_workflow(payload: Dict[str, Any]):
    """Validate graph structure, node connections, and permission consistency."""
    if "entry_node_id" in payload:
        wf = WorkflowConfig(**payload)
        res = GraphValidator().validate(wf)
        return {
            "is_valid": res.is_valid,
            "valid": res.is_valid,
            "errors": res.errors,
            "warnings": res.warnings,
        }
    else:
        data = payload.get("definition") or payload
        definition = WorkflowDefinition(**data)
        errors = validate_workflow_definition(definition)
        return {
            "valid": len(errors) == 0,
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": [],
        }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow(payload: Dict[str, Any]):
    """Save a validated workflow configuration."""
    if "definition" in payload:
        create_req = WorkflowCreate(**payload)
        errors = validate_workflow_definition(create_req.definition)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"errors": errors},
            )
        wf_id = f"wf-{len(_WORKFLOWS) + 1}"
        wf_res = WorkflowResponse(id=wf_id, name=create_req.name, definition=create_req.definition)
        _WORKFLOWS[wf_id] = wf_res
        return wf_res
    else:
        wf_config = WorkflowConfig(**payload)
        validator = GraphValidator()
        validation = validator.validate(wf_config)
        if not validation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Invalid workflow configuration", "errors": validation.errors},
            )
        _WORKFLOWS_STORE[wf_config.workflow_id] = wf_config
        return wf_config


@router.get("")
async def list_workflows():
    """List all saved workflows."""
    results = list(_WORKFLOWS.values()) + list(_WORKFLOWS_STORE.values())
    return results


@router.get("/{wf_id}")
async def get_workflow(wf_id: str):
    """Retrieve a specific workflow by ID."""
    if wf_id in _WORKFLOWS:
        return _WORKFLOWS[wf_id]
    if wf_id in _WORKFLOWS_STORE:
        return _WORKFLOWS_STORE[wf_id]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")


@router.put("/{wf_id}", response_model=WorkflowResponse)
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
                detail={"errors": errors},
            )

    updated_wf = WorkflowResponse(id=wf_id, name=new_name, definition=new_def)
    _WORKFLOWS[wf_id] = updated_wf
    return updated_wf
