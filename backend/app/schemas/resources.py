"""Controlled resource and tool action schemas."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from .provenance import ProvenanceRecord


class ResourceActionType(str, Enum):
    """Category of resource operation."""
    TOOL_CALL = "tool_call"
    DB_READ = "db_read"
    DB_WRITE = "db_write"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"


class ResourceActionRequest(BaseModel):
    """Request submitted to the Controlled Resource Gateway."""
    action_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str = Field(...)
    trace_id: str = Field(...)
    requester_id: str = Field(..., description="ID of requesting agent node")
    action_type: ResourceActionType = Field(...)
    resource_name: str = Field(..., description="Target tool or resource name")
    operation: str = Field(..., description="Specific function or method to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Validated arguments")
    provenance: Optional[ProvenanceRecord] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResourceActionResult(BaseModel):
    """Result returned after authorized execution through an adapter."""
    action_id: str = Field(...)
    success: bool = Field(...)
    data: Optional[Any] = Field(default=None)
    error: Optional[str] = Field(default=None)
    duration_ms: float = Field(default=0.0)
    provenance: ProvenanceRecord = Field(...)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
