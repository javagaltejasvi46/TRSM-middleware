from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class RunStart(BaseModel):
    workflow_id: str = Field(..., description="ID of the workflow to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Initial parameters / input state")

class NodeRunLog(BaseModel):
    node_id: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None

class RunResponse(BaseModel):
    run_id: str
    workflow_id: str
    status: str = "pending"  # pending, running, completed, failed
    state: Dict[str, Any] = Field(default_factory=dict)
    execution_history: List[NodeRunLog] = Field(default_factory=list)
    gateway_events: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
