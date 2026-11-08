from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class AgentNodeConfig(BaseModel):
    id: str = Field(..., description="Unique identifier for the agent node")
    role: str = Field(..., description="Role of the agent (e.g. backend, db_manager, qa, devops)")
    model: str = Field(..., description="LLM/model identifier or adapter type (e.g. mock, llama3, qwen)")
    node_type: str = Field(default="agent", description="Type of node: agent, human, or resource")
    allowed_peers: List[str] = Field(default_factory=list, description="Explicit list of peer node IDs this agent can send messages to")
    allowed_resources: List[str] = Field(default_factory=list, description="Allowed tool or database identifiers")
    system_prompt: Optional[str] = Field(None, description="Optional custom system prompt")

class EdgeConfig(BaseModel):
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")

class WorkflowDefinition(BaseModel):
    nodes: List[AgentNodeConfig] = Field(..., description="List of nodes in the workflow")
    edges: List[EdgeConfig] = Field(default_factory=list, description="Directed communication edges between nodes")
    entry_point: Optional[str] = Field(None, description="Starting agent node ID for execution")

class WorkflowCreate(BaseModel):
    name: str = Field(..., description="Human-readable workflow name")
    definition: WorkflowDefinition = Field(..., description="Validated workflow definition")

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    definition: Optional[WorkflowDefinition] = None

class WorkflowResponse(BaseModel):
    id: str
    name: str
    definition: WorkflowDefinition
