"""Workflow execution runs API routes."""

from typing import Any, Dict, List, Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...schemas.workflow import WorkflowConfig
from ...services.run_service import RunService

router = APIRouter(prefix="/api/runs", tags=["Runs"])


class StartRunRequest(BaseModel):
    """Payload to initiate a workflow run."""
    workflow_id: Optional[str] = None
    workflow: Optional[WorkflowConfig] = None
    task: str = Field(..., description="Initial task prompt given to entry agent")
    enable_trsm: bool = Field(default=True, description="Enable TRSM mediation (False for baseline)")


class RunSummaryResponse(BaseModel):
    """Summary of a workflow execution run."""
    run_id: str
    workflow_id: str
    status: str
    enable_trsm: bool
    task: str
    total_messages: int
    total_tool_calls: int
    blocked_actions: int


@router.post("", response_model=RunSummaryResponse, status_code=status.HTTP_201_CREATED)
async def start_run(request: StartRunRequest):
    """Start execution of a workflow run."""
    run_service = RunService()
    return await run_service.start_run(request)


@router.get("/{run_id}", response_model=RunSummaryResponse)
async def get_run(run_id: str):
    """Retrieve run execution summary."""
    run_service = RunService()
    run = await run_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run
