"""Baseline (unprotected) trial executor."""

import time
from typing import Any, Dict
from ..runtime.orchestrator import Orchestrator
from ..schemas.workflow import WorkflowConfig


class BaselineTrialExecutor:
    """Executes a scenario trial with TRSM gateways and policy engine bypassed."""

    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator

    async def execute_trial(
        self, scenario: Dict[str, Any], workflow: WorkflowConfig
    ) -> Dict[str, Any]:
        """Execute scenario in baseline mode."""
        start_t = time.time()
        initial_task = scenario.get("initial_task", "")

        result = await self.orchestrator.run_workflow(
            workflow=workflow,
            initial_task=initial_task,
            enable_trsm=False,
        )
        duration_ms = (time.time() - start_t) * 1000.0

        # In baseline, if an adversarial objective was present, did it succeed?
        # Since TRSM was off, blocked_actions is 0 and actions executed unhindered
        adversarial_success = (
            scenario.get("ground_truth_label") == "adversarial"
            and result["blocked_actions"] == 0
        )

        return {
            "trial_id": result["run_id"],
            "scenario_id": scenario.get("id"),
            "mode": "baseline",
            "ground_truth_label": scenario.get("ground_truth_label"),
            "status": result["status"],
            "total_messages": result["total_messages"],
            "total_tool_calls": result["total_tool_calls"],
            "blocked_actions": result["blocked_actions"],
            "duration_ms": round(duration_ms, 2),
            "adversarial_objective_achieved": adversarial_success,
        }
