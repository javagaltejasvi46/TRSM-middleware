"""Decision evidence models and helpers for TRSM Policy Engine."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ..schemas.threats import ThreatFinding


class RuleEvaluationResult(BaseModel):
    """Result of evaluating a single declarative policy rule."""
    rule_id: str
    rule_name: str
    passed: bool
    reason_code: str
    details: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvidence(BaseModel):
    """Consolidated evidence supporting an authoritative policy decision."""
    matched_rule_ids: List[str] = Field(default_factory=list)
    rule_results: List[RuleEvaluationResult] = Field(default_factory=list)
    threat_findings: List[ThreatFinding] = Field(default_factory=list)
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    provenance_risk: Optional[str] = None
    context_summary: Dict[str, Any] = Field(default_factory=dict)
