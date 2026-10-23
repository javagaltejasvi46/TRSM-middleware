# API Contracts Specification

## HTTP Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status |
| `POST` | `/api/workflows/validate` | Validates a workflow JSON without running it |
| `POST` | `/api/workflows` | Saves a new workflow definition |
| `GET` | `/api/workflows/{workflow_id}` | Retrieves a saved workflow definition |
| `GET` | `/api/workflows` | Lists available workflows |
| `POST` | `/api/runs` | Triggers execution of a workflow run |
| `GET` | `/api/runs/{run_id}` | Retrieves execution status and summary |
| `GET` | `/api/runs/{run_id}/events` | Fetches filtered audit events for a run |
| `GET` | `/api/runs/{run_id}/trace` | Reconstructs causal trace graph for run |
| `GET` | `/api/runs/{run_id}/metrics` | Returns computed CSS, TUE, latency, and security metrics |
| `POST` | `/api/evaluations/compare` | Compares baseline vs. protected run metrics |
| `POST` | `/api/reviews/{review_id}/resolve` | Resolves a paused HITL review state |
