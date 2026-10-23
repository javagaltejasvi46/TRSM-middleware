"""Persistence domain model definitions."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class WorkflowRecord:
    workflow_id: str
    name: str
    version: str
    definition: Dict[str, Any]


@dataclass
class RunRecord:
    run_id: str
    workflow_id: str
    status: str
    enable_trsm: bool
    task: str
    summary: Optional[Dict[str, Any]] = None
