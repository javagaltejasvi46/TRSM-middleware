"""Pytest fixtures and configuration."""

import pytest
from app.schemas.agent import AgentNodeConfig, AgentRole
from app.schemas.workflow import WorkflowConfig, WorkflowEdge


@pytest.fixture
def sample_workflow() -> WorkflowConfig:
    """Fixture providing a standard 3-agent software engineering workflow."""
    backend_node = AgentNodeConfig(
        node_id="backend_agent",
        name="Backend Agent",
        role=AgentRole.BACKEND,
        allowed_peers=["db_manager_agent"],
        allowed_tools=["customer_db"],
    )
    db_node = AgentNodeConfig(
        node_id="db_manager_agent",
        name="DB Manager Agent",
        role=AgentRole.DB_MANAGER,
        allowed_peers=["qa_agent"],
        allowed_tools=["customer_db", "workflow_memory"],
    )
    qa_node = AgentNodeConfig(
        node_id="qa_agent",
        name="QA Agent",
        role=AgentRole.QA,
        allowed_peers=[],
        allowed_tools=["test_suite"],
    )
    return WorkflowConfig(
        workflow_id="test_workflow_001",
        name="Test Workflow",
        entry_node_id="backend_agent",
        nodes=[backend_node, db_node, qa_node],
        edges=[
            WorkflowEdge(source_node_id="backend_agent", target_node_id="db_manager_agent"),
            WorkflowEdge(source_node_id="db_manager_agent", target_node_id="qa_agent"),
        ],
    )
