"""Provenance tracking contracts and trust labels."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TrustLabel(str, Enum):
    """Canonical trust and origin labels."""
    TRUSTED_POLICY = "trusted_policy"
    USER_INPUT = "user_input"
    UNTRUSTED_EXTERNAL = "untrusted_external"
    AGENT_GENERATED = "agent_generated"
    TOOL_RESULT = "tool_result"
    VALIDATED = "validated"


class ProvenanceRecord(BaseModel):
    """Lineage and trust metadata attached to messages and tool results."""
    origin_type: TrustLabel = Field(..., description="Primary classification of origin")
    source_event_ids: List[str] = Field(default_factory=list, description="Direct upstream event IDs")
    trust_labels: List[TrustLabel] = Field(default_factory=list, description="Set of associated trust tags")
    lineage_path: List[str] = Field(default_factory=list, description="Chain of agent/tool nodes touched")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
