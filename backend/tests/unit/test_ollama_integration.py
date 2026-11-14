"""Test suite for Ollama adapter and orchestrator LLM integration."""

import pytest
from unittest.mock import AsyncMock, patch

from backend.app.runtime.adapters.ollama_adapter import OllamaAdapter
from backend.app.runtime.orchestrator import Orchestrator
from backend.app.schemas.agent import AgentNodeConfig, AgentRole
from backend.app.schemas.workflow import WorkflowConfig


@pytest.mark.asyncio
async def test_ollama_adapter_availability_check():
    adapter = OllamaAdapter("http://127.0.0.1:11434")
    # When daemon is down, returns False gracefully
    available = await adapter.is_available()
    assert isinstance(available, bool)


@pytest.mark.asyncio
async def test_orchestrator_queries_ollama_when_available():
    mock_ollama = AsyncMock(spec=OllamaAdapter)
    mock_ollama.is_available.return_value = True
    mock_ollama.generate.return_value = "OLLAMA_GENERATED_RESPONSE"

    orch = Orchestrator(ollama_adapter=mock_ollama)

    workflow = WorkflowConfig(
        workflow_id="wf_ollama_test",
        name="Ollama Test",
        version="1.0.0",
        entry_node_id="agent_1",
        nodes=[
            AgentNodeConfig(
                node_id="agent_1",
                name="Ingest Agent",
                role=AgentRole.CUSTOM,
                model="llama3.2:1b",
                allowed_peers=["agent_2"],
            ),
            AgentNodeConfig(
                node_id="agent_2",
                name="Worker Agent",
                role=AgentRole.BACKEND,
                model="llama3.2:1b",
                allowed_peers=[],
            ),
        ],
    )

    result = await orch.run_workflow(
        workflow=workflow,
        initial_task="Test live LLM generation",
        enable_trsm=False,
    )

    assert result["status"] == "completed"
    assert mock_ollama.is_available.called
    assert mock_ollama.generate.called


@pytest.mark.asyncio
async def test_orchestrator_falls_back_to_mock_when_ollama_down():
    mock_ollama = AsyncMock(spec=OllamaAdapter)
    mock_ollama.is_available.return_value = False

    orch = Orchestrator(ollama_adapter=mock_ollama)

    workflow = WorkflowConfig(
        workflow_id="wf_fallback_test",
        name="Fallback Test",
        version="1.0.0",
        entry_node_id="agent_1",
        nodes=[
            AgentNodeConfig(
                node_id="agent_1",
                name="Agent 1",
                role=AgentRole.BACKEND,
                model="llama3.2:1b",
                allowed_peers=["agent_2"],
            ),
            AgentNodeConfig(
                node_id="agent_2",
                name="Agent 2",
                role=AgentRole.DB_MANAGER,
                model="llama3.2:1b",
                allowed_peers=[],
            ),
        ],
    )

    result = await orch.run_workflow(
        workflow=workflow,
        initial_task="Retrieve customer profile",
        enable_trsm=False,
    )

    assert result["status"] == "completed"
    assert mock_ollama.is_available.called
    # Since Ollama is down, generate is not called and mock adapter handles it
    assert not mock_ollama.generate.called

