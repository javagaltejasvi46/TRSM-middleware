"""Optional Human-in-the-Loop review resolution routes."""

from fastapi import APIRouter
from pydantic import BaseModel

from ...schemas.policy import PolicyDecisionEnum

router = APIRouter(prefix="/api/reviews", tags=["Human Review"])


class ResolveReviewRequest(BaseModel):
    decision: PolicyDecisionEnum
    reviewer_comment: str


@router.post("/{review_id}/resolve")
async def resolve_review(review_id: str, request: ResolveReviewRequest):
    """Resolve a review-required state."""
    return {
        "review_id": review_id,
        "resolved_decision": request.decision,
        "comment": request.reviewer_comment,
        "status": "resolved",
    }
