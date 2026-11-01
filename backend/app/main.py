from fastapi import FastAPI

app = FastAPI()

# Include API routers
from backend.app.api import workflows, runs, events
app.include_router(workflows.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(events.router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

