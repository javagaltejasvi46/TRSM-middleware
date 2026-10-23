# ADR 0003: Backend Canonical Contract Ownership

## Context
In full-stack applications with machine learning or agentic backends, contract drift between client TypeScript interfaces, server serializers, and internal agent models is a frequent source of bugs and security vulnerabilities.

## Decision
The Python backend owns all canonical data contracts via **Pydantic schemas** in `backend/app/schemas/`. 

## Rules
1. No module passes unvalidated dictionaries across component boundaries.
2. The frontend types in `frontend/src/types/` are derived from the FastAPI OpenAPI schema.
3. Changes to shared wire models (such as `WorkflowConfig`, `AgentMessageProposal`, `PolicyDecision`, `AuditEvent`) require agreement among Tejasvi, Yashwanth, and Debarshi.
