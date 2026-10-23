# ADR 0001: Monorepo Architecture for TRSM

## Context
TRSM consists of a visual workflow playground frontend, a Python FastAPI execution backend, a LangGraph runtime, TRSM policy/guardian logic, and audit persistence. We needed to choose between a microservices repository split or a single monorepo.

## Decision
We chose a **single monorepo** layout containing both `frontend/` and `backend/`. 

## Rationale
1. Simplifies schema synchronization between Pydantic models in the backend and TypeScript types in the frontend.
2. Avoids premature microservice boundaries (gateway, policy engine, audit collector, and metrics engine all live inside the backend application).
3. Eases local developer setup and reproducible benchmarking.

## Consequences
- Requires clear internal module boundaries and discipline across team ownership (Tejasvi, Yashwanth, Debarshi).
- Root-level configuration (.gitignore, Makefile, CI) coordinates both Python and Node ecosystems.
