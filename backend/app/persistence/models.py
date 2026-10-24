"""Persistence domain model definitions."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class WorkflowRecord:
    workflow_id: str
    name: str
    version: str
    definition: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class RunRecord:
    run_id: str
    workflow_id: str
    status: str
    enable_trsm: bool
    task: str
    summary: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class ReviewRecord:
    review_id: str
    run_id: str
    trace_id: str
    event_id: str
    actor_id: str
    action_type: str
    target: str
    status: str
    decision: Optional[str] = None
    reviewer_comment: Optional[str] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
