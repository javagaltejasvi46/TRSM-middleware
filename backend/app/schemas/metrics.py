"""Evaluation metrics schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MetricResult(BaseModel):
    """Result of a single calculated evaluation metric."""
    name: str = Field(...)
    version: str = Field(default="1.0.0")
    value: Optional[float] = Field(default=None)
    available: bool = Field(default=True)
    unavailable_reason: Optional[str] = Field(default=None)
    numerator: Optional[float] = Field(default=None)
    denominator: Optional[float] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunMetrics(BaseModel):
    """Aggregate metric results for an individual workflow execution run."""
    run_id: str = Field(...)
    css: MetricResult = Field(..., description="Component Synergy Score")
    tue: MetricResult = Field(..., description="Tool Utilization Efficacy")
    task_success: bool = Field(default=False)
    security_blocked_attacks: int = Field(default=0)
    total_messages: int = Field(default=0)
    total_tool_calls: int = Field(default=0)
    avg_latency_ms: float = Field(default=0.0)
    p95_latency_ms: float = Field(default=0.0)
