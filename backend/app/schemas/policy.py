"""Canonical policy decision models and enums."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class PolicyDecisionEnum(str, Enum):
    """The four authoritative policy decisions recognized across TRSM."""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    QUARANTINE = "QUARANTINE"
    REVIEW = "REVIEW"


class PolicyDecision(BaseModel):
    """Authoritative decision emitted by the Policy Enforcement Engine."""
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str = Field(..., description="ID of the message proposal or resource action")
    outcome: PolicyDecisionEnum = Field(..., description="Authoritative outcome")
    reason_code: str = Field(..., description="Standard machine-readable reason code")
    evidence: Optional[Dict[str, Any]] = Field(default=None, description="Structured decision evidence")
    applicable_rule_ids: List[str] = Field(default_factory=list, description="IDs of rules evaluated")
    policy_version: str = Field(default="1.0.0", description="Version of the active policy specification")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
