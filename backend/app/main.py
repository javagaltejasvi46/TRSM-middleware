from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.app.persistence.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema on startup
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# Include API routers
from backend.app.api import workflows, runs, events
app.include_router(workflows.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(events.router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
