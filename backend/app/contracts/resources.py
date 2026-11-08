from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ResourceType(str, Enum):
    TOOL = "TOOL"
    DATABASE = "DATABASE"
    MEMORY = "MEMORY"

class ResourceAction(BaseModel):
    action_type: ResourceType
    resource_id: str  # e.g., "db_query", "memory_store", "shell_exec"
    actor_id: str     # Agent node ID initiating action
    actor_role: str   # Agent role (backend, db_manager, etc.)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    operation: str = "execute"  # read, write, execute

class ResourceExecutionResult(BaseModel):
    action_id: str
    resource_id: str
    actor_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)
