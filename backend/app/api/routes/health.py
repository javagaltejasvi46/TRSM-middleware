"""Health check endpoint."""

from fastapi import APIRouter
from ...config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Return runtime service health and policy engine version."""
    return {
        "status": "healthy",
        "service": "TRSM Middleware",
        "environment": settings.ENVIRONMENT,
        "policy_version": settings.POLICY_VERSION,
    }
