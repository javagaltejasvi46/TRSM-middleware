from fastapi import APIRouter, HTTPException, status
from typing import List
from backend.app.contracts.run import RunStart, RunResponse
from backend.app.api.workflows import _WORKFLOWS
from backend.app.runtime.orchestrator import orchestrator

router = APIRouter()

@router.post("/runs", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def start_run(payload: RunStart):
    wf_record = _WORKFLOWS.get(payload.workflow_id)
    if not wf_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{payload.workflow_id}' not found. Cannot start run."
        )

    run_result = orchestrator.execute_workflow(
        workflow_id=payload.workflow_id,
        workflow=wf_record.definition,
        initial_params=payload.parameters
    )
    return run_result

@router.get("/runs", response_model=List[RunResponse])
async def list_runs():
    return orchestrator.list_runs()

@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str):
    run_record = orchestrator.get_run(run_id)
    if not run_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with ID '{run_id}' not found."
        )
    return run_record
