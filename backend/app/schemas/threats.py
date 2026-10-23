"""Threat findings emitted by the Runtime Guardian."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from .policy import PolicyDecisionEnum


class ThreatFamily(str, Enum):
    """The core threat families detected by TRSM."""
    PROMPT_INJECTION = "prompt_injection"
    MEMORY_POISONING = "memory_poisoning"
    ROLE_HIJACKING = "role_hijacking"
    UNAUTHORIZED_RESOURCE = "unauthorized_resource"


class ThreatSeverity(str, Enum):
    """Severity classification for threat findings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatFinding(BaseModel):
    """Structured threat finding emitted by detection components."""
    finding_id: str = Field(default_factory=lambda: str(uuid4()))
    threat_family: ThreatFamily = Field(...)
    severity: ThreatSeverity = Field(...)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_event_id: str = Field(...)
    evidence_summary: str = Field(...)
    raw_evidence: Optional[Dict[str, Any]] = Field(default=None)
    recommended_action: PolicyDecisionEnum = Field(default=PolicyDecisionEnum.BLOCK)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
