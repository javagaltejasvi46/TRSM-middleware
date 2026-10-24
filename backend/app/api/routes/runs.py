"""Workflow execution runs API routes."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
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
    use_ollama: bool = Field(default=False, description="Use local Ollama model instead of deterministic mock")


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


class RunStatusResponse(BaseModel):
    """Current status of an execution run."""
    run_id: str
    workflow_id: str
    status: str
    enable_trsm: bool


@router.post("", response_model=RunSummaryResponse, status_code=status.HTTP_201_CREATED)
async def start_run(request: StartRunRequest):
    """Start execution of a workflow run."""
    run_service = RunService()
    return await run_service.start_run(request)


@router.get("", response_model=List[RunSummaryResponse])
async def list_runs(limit: int = Query(default=50, ge=1, le=200)):
    """List recent workflow execution runs."""
    run_service = RunService()
    runs = await run_service.list_runs(limit=limit)
    return [
        RunSummaryResponse(
            run_id=r["run_id"],
            workflow_id=r["workflow_id"],
            status=r["status"],
            enable_trsm=r["enable_trsm"],
            task=r["task"],
            total_messages=r.get("total_messages", 0),
            total_tool_calls=r.get("total_tool_calls", 0),
            blocked_actions=r.get("blocked_actions", 0),
        )
        for r in runs
    ]


@router.get("/{run_id}", response_model=RunSummaryResponse)
async def get_run(run_id: str):
    """Retrieve run execution summary."""
    run_service = RunService()
    run = await run_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.get("/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(run_id: str):
    """Retrieve lightweight status for polling or node canvas updates."""
    run_service = RunService()
    run = await run_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return RunStatusResponse(
        run_id=run["run_id"],
        workflow_id=run["workflow_id"],
        status=run["status"],
        enable_trsm=run["enable_trsm"],
    )
