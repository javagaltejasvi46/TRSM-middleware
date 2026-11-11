from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class AuditEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    run_id: str = Field(..., description="ID of the workflow run")
    trace_id: str = Field(..., description="Distributed trace or causality chain ID")
    parent_event_id: Optional[str] = Field(None, description="Causal parent event ID")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    
    event_type: str = Field(..., description="Type of event: MESSAGE_PROPOSAL, GATEWAY_DECISION, TOOL_EXECUTION, NODE_START, NODE_END, RUN_START, RUN_END")
    actor_id: str = Field(..., description="Initiating agent node or system component ID")
    target_id: Optional[str] = Field(None, description="Target recipient or resource ID")
    source_type: str = Field(default="agent", description="Source type: agent, gateway, tool, orchestrator")
    trust_labels: List[str] = Field(default_factory=list, description="Security/trust labels (e.g. untrusted_input, verified)")
    
    policy_decision: Optional[str] = Field(None, description="ALLOW, BLOCK, QUARANTINE, REVIEW")
    reason_code: Optional[str] = Field(None, description="Code explaining policy decision")
    policy_version: Optional[str] = Field("v1.0", description="Version of the policy rule")
    
    duration_ms: Optional[float] = Field(None, description="Execution duration in milliseconds")
    safe_payload_summary: Optional[str] = Field(None, description="Redacted or safe summary preview")
    payload_reference: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata or structured payload references")

