"""Agent node definitions and state models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Standard demonstrated agent roles in TRSM."""
    BACKEND = "backend"
    DB_MANAGER = "db_manager"
    QA = "qa"
    DEVOPS = "devops"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    """Agent runtime execution state."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    QUARANTINED = "quarantined"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"


class AgentNodeConfig(BaseModel):
    """Configuration for an individual agent in a workflow."""
    node_id: str = Field(..., description="Unique ID within the workflow")
    name: str = Field(..., description="Human-readable node title")
    role: AgentRole = Field(default=AgentRole.CUSTOM, description="Designated agent role")
    model: str = Field(default="mock", description="Model identifier (e.g. llama3:8b, mock)")
    instructions: str = Field(default="", description="Base system instructions for the agent")
    allowed_peers: List[str] = Field(default_factory=list, description="IDs of agents this node can message")
    allowed_tools: List[str] = Field(default_factory=list, description="Names of tools this node can invoke")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Execution timeout in seconds")
    call_limit: int = Field(default=10, ge=1, le=100, description="Maximum allowed message or tool calls")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom node properties")
