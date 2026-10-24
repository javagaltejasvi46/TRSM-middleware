"""Human-in-the-Loop review management and resolution routes."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...persistence.review_repository import ReviewRepository
from ...schemas.policy import PolicyDecisionEnum

router = APIRouter(prefix="/api/reviews", tags=["Human Review"])


class ReviewResponse(BaseModel):
    review_id: str
    run_id: str
    trace_id: str
    event_id: str
    actor_id: str
    action_type: str
    target: str
    status: str
    decision: Optional[str] = None
    reviewer_comment: Optional[str] = None


class ResolveReviewRequest(BaseModel):
    decision: PolicyDecisionEnum = Field(..., description="Approved resolution decision (ALLOW or BLOCK)")
    reviewer_comment: str = Field(..., description="Reviewer notes or reason for resolution")


@router.get("", response_model=List[ReviewResponse])
async def list_pending_reviews():
    """List all pending Human-in-the-Loop reviews requiring resolution."""
    repo = ReviewRepository()
    records = await repo.list_pending_reviews()
    return [
        ReviewResponse(
            review_id=r.review_id,
            run_id=r.run_id,
            trace_id=r.trace_id,
            event_id=r.event_id,
            actor_id=r.actor_id,
            action_type=r.action_type,
            target=r.target,
            status=r.status,
            decision=r.decision,
            reviewer_comment=r.reviewer_comment,
        )
        for r in records
    ]


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: str):
    """Retrieve details of a specific review by review_id."""
    repo = ReviewRepository()
    record = await repo.get_review(review_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return ReviewResponse(
        review_id=record.review_id,
        run_id=record.run_id,
        trace_id=record.trace_id,
        event_id=record.event_id,
        actor_id=record.actor_id,
        action_type=record.action_type,
        target=record.target,
        status=record.status,
        decision=record.decision,
        reviewer_comment=record.reviewer_comment,
    )


@router.post("/{review_id}/resolve", response_model=ReviewResponse)
async def resolve_review(review_id: str, request: ResolveReviewRequest):
    """Resolve a review-required state with an authoritative decision."""
    repo = ReviewRepository()
    record = await repo.resolve_review(
        review_id=review_id,
        decision=request.decision.value,
        comment=request.reviewer_comment,
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return ReviewResponse(
        review_id=record.review_id,
        run_id=record.run_id,
        trace_id=record.trace_id,
        event_id=record.event_id,
        actor_id=record.actor_id,
        action_type=record.action_type,
        target=record.target,
        status=record.status,
        decision=record.decision,
        reviewer_comment=record.reviewer_comment,
    )
