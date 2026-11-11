from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentMessageProposal(BaseModel):
    sender: str
    recipient: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentExecutionResult(BaseModel):
    node_id: str
    status: str = "success"  # "success" or "error"
    output_message: Optional[str] = None
    proposed_messages: List[AgentMessageProposal] = Field(default_factory=list)
    error_message: Optional[str] = None

