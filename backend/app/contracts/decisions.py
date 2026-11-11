from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DecisionType(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    QUARANTINE = "QUARANTINE"
    REVIEW = "REVIEW"

class ThreatFinding(BaseModel):
    threat_type: str
    severity: str  # low, medium, high, critical
    details: str
    confidence: float = 1.0

class PolicyDecision(BaseModel):
    decision: DecisionType
    reason_code: str
    policy_version: str = "v1.0"
    threat_findings: List[ThreatFinding] = Field(default_factory=list)
    redacted_content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

