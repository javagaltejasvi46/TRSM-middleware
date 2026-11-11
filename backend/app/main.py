"""FastAPI Application entrypoint for TRSM Middleware."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .persistence.db import init_db
from .persistence.database import init_db as init_db_sync
from .api.routes import (
    events_router,
    health_router,
    metrics_router,
    reviews_router,
    runs_router,
    workflows_router,
)
from .api.events import router as audit_events_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context (initialization & teardown)."""
    # Startup: Initialize SQLite schemas and connections
    await init_db()
    try:
        init_db_sync()
    except Exception:
        pass
    yield


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="TRSM Middleware API",
        description="Trust, Risk, and Security Management for LLM-Based Multi-Agent Systems",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS for frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API Routers
    app.include_router(health_router)
    app.include_router(workflows_router)
    app.include_router(runs_router)
    app.include_router(events_router)
    app.include_router(metrics_router)
    app.include_router(reviews_router)

    # Register Audit Events query router
    app.include_router(audit_events_router, prefix="/api")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
