# ADR 0002: LangGraph Runtime for Multi-Agent Orchestration

## Context
Multi-agent systems require stateful orchestration, support for cyclical execution, and structured state transitions. We evaluated raw Python asyncio loops, AutoGen, CrewAI, and LangGraph.

## Decision
Adopt **LangGraph** as the primary backend orchestration engine, encapsulated behind an internal `orchestrator.py` and `graph_compiler.py` boundary.

## Rationale
1. LangGraph represents workflows as directed graphs with explicit state management, mapping cleanly to visual node graphs.
2. It allows wrapping node execution hooks with the TRSM Node Guard and Central Communication Gateway.
3. It natively supports deterministic test graphs without requiring live LLM calls.

## Consequences
- Workflows must be validated server-side to ensure graphs are acyclic or bounded in execution depth before compilation.
