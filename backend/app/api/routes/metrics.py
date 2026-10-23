"""Metrics and evaluation comparison API routes."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...schemas.metrics import RunMetrics
from ...services.evaluation_service import EvaluationService

router = APIRouter(tags=["Metrics & Evaluation"])


class RunComparisonResult(BaseModel):
    baseline_run_id: str
    protected_run_id: str
    baseline_metrics: RunMetrics
    protected_metrics: RunMetrics
    overhead_ms: float
    security_delta: str


@router.get("/api/runs/{run_id}/metrics", response_model=RunMetrics)
async def get_run_metrics(run_id: str):
    """Retrieve computed CSS, TUE, latency, and security metrics for a run."""
    eval_service = EvaluationService()
    metrics = await eval_service.calculate_run_metrics(run_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Metrics not found for run")
    return metrics


@router.get("/api/evaluations/compare", response_model=RunComparisonResult)
async def compare_runs(
    baseline_run: str = Query(..., description="Run ID executed without TRSM"),
    protected_run: str = Query(..., description="Run ID executed with TRSM active"),
):
    """Compare baseline vs. protected run metrics."""
    eval_service = EvaluationService()
    return await eval_service.compare_runs(baseline_run, protected_run)
