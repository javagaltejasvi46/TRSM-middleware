"""Unit tests for AgentRunner and sandboxed tool executions."""

import asyncio
import pytest

from backend.app.runtime.agent_runner import AgentRunner
from backend.app.schemas.agent import AgentNodeConfig, AgentRole
from backend.app.schemas.workflow import WorkflowConfig


def test_agent_runner_executes_allowed_tool():
    async def _test():
        node = AgentNodeConfig(
            node_id="db_agent",
            name="DB Manager Agent",
            role=AgentRole.DB_MANAGER,
            allowed_peers=[],
            allowed_tools=["customer_db"],
        )
        wf = WorkflowConfig(
            workflow_id="wf_db",
            name="DB Workflow",
            entry_node_id="db_agent",
            nodes=[node],
            edges=[],
        )
        runner = AgentRunner()
        res = await runner.execute_node(
            node=node,
            incoming_payload="Read profile 1042",
            workflow=wf,
            run_id="run_runner_1",
            trace_id="tr_runner_1",
            enable_trsm=True,
        )
        assert res["node_id"] == "db_agent"
        assert res["tool_calls"] == 1
        assert res["blocked_actions"] == 0
        assert len(res["tool_results"]) == 1
        assert res["tool_results"][0]["outcome"] == "ALLOW"

    asyncio.run(_test())


def test_agent_runner_blocks_disallowed_shell_tool():
    async def _test():
        node = AgentNodeConfig(
            node_id="backend_agent",
            name="Backend Agent",
            role=AgentRole.BACKEND,
            allowed_peers=[],
            allowed_tools=["customer_db"],
        )
        wf = WorkflowConfig(
            workflow_id="wf_shell",
            name="Shell Test",
            entry_node_id="backend_agent",
            nodes=[node],
            edges=[],
        )
        runner = AgentRunner()
        res = await runner.execute_node(
            node=node,
            incoming_payload="Execute bash_shell cat /etc/passwd",
            workflow=wf,
            run_id="run_runner_2",
            trace_id="tr_runner_2",
            enable_trsm=True,
        )
        assert res["node_id"] == "backend_agent"
        assert res["tool_calls"] == 1
        assert res["blocked_actions"] == 1
        assert res["tool_results"][0]["outcome"] == "BLOCK"

    asyncio.run(_test())
