"""FastAPI Application entrypoint for TRSM Middleware."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api.routes import (
    events_router,
    health_router,
    metrics_router,
    reviews_router,
    runs_router,
    workflows_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context (initialization & teardown)."""
    # Startup: Initialize SQLite schemas and connections if necessary
    yield
    # Shutdown: Flush event queues and cleanup connections


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

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
