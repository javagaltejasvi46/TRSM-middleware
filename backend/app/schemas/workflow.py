"""Workflow graph configuration and validation schemas."""

from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from .agent import AgentNodeConfig


class WorkflowEdge(BaseModel):
    """A configured visual or communication edge between two nodes."""
    source_node_id: str = Field(..., description="Sender or originating node ID")
    target_node_id: str = Field(..., description="Recipient or target node ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Edge metadata")


class WorkflowConfig(BaseModel):
    """Complete workflow definition created or loaded by the playground."""
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(default="New Multi-Agent Workflow")
    version: str = Field(default="1.0.0")
    description: str = Field(default="")
    entry_node_id: str = Field(..., description="ID of node that receives initial task prompt")
    nodes: List[AgentNodeConfig] = Field(..., min_length=1, description="List of configured agent nodes")
    edges: List[WorkflowEdge] = Field(default_factory=list, description="List of configured routes between nodes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom workflow parameters")


class WorkflowValidationResult(BaseModel):
    """Result of server-side workflow structure and permission validation."""
    is_valid: bool = Field(..., description="True if workflow passed all safety and graph checks")
    errors: List[str] = Field(default_factory=list, description="Blocking validation issues")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking recommendations")
