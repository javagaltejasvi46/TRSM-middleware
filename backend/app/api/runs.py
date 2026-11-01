from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict

router = APIRouter()

class RunStart(BaseModel):
    workflow_id: str = Field(..., description="ID of the workflow to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Optional run parameters")

class RunResponse(BaseModel):
    run_id: str
    status: str = "pending"
    workflow_id: str

# Simple in‑memory store for demo purposes
_RUNS: dict[str, RunResponse] = {}

@router.post("/runs", response_model=RunResponse)
async def start_run(payload: RunStart):
    run_id = f"run-{len(_RUNS)+1}"
    run = RunResponse(run_id=run_id, workflow_id=payload.workflow_id)
    _RUNS[run_id] = run
    return run

@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str):
    run = _RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

