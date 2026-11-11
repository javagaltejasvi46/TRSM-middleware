"""Workflow execution runs API routes (Unified)."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.contracts.run import RunResponse, RunStart
from backend.app.api.workflows import _WORKFLOWS
from backend.app.runtime.orchestrator import orchestrator
from ..schemas.workflow import WorkflowConfig
from ..services.run_service import RunService

router = APIRouter(prefix="/api/runs", tags=["Runs"])


class StartRunRequest(BaseModel):
    """Payload to initiate a workflow run."""
    workflow_id: Optional[str] = None
    workflow: Optional[WorkflowConfig] = None
    task: Optional[str] = Field(default=None, description="Initial task prompt given to entry agent")
    enable_trsm: bool = Field(default=True, description="Enable TRSM mediation (False for baseline)")
    parameters: Optional[Dict[str, Any]] = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def start_run(payload: Dict[str, Any]):
    """Start execution of a workflow run."""
    if not payload.get("workflow_id") and not payload.get("task"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required fields: workflow_id or task must be provided",
        )

    # Check if this is Yashwanth's RunStart format (or parameters provided without task)
    if "parameters" in payload or (payload.get("workflow_id") and not payload.get("task")):
        wf_id = payload.get("workflow_id")
        wf_record = _WORKFLOWS.get(wf_id)
        if not wf_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow with ID '{wf_id}' not found. Cannot start run.",
            )

        run_result = orchestrator.execute_workflow(
            workflow_id=wf_id,
            workflow=wf_record.definition,
            initial_params=payload.get("parameters") or {},
        )
        return run_result

    # Otherwise, it's Main's StartRunRequest format
    run_service = RunService()
    req = StartRunRequest(**payload)
    return await run_service.start_run(req)


@router.get("")
async def list_runs():
    """List all workflow runs."""
    yashwanth_runs = orchestrator.list_runs()
    try:
        run_service = RunService()
        main_runs = await run_service.list_runs()
    except Exception:
        main_runs = []
    return list(yashwanth_runs) + list(main_runs)


@router.get("/{run_id}")
async def get_run(run_id: str):
    """Retrieve run execution summary or response."""
    run_record = orchestrator.get_run(run_id)
    if run_record:
        return run_record

    try:
        run_service = RunService()
        run = await run_service.get_run(run_id)
        if run:
            return run
    except Exception:
        pass

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run with ID '{run_id}' not found.")
