"""Repeatable evaluation runner executing matched baseline and protected scenario suites."""

import glob
import os
from typing import Any, Dict, List, Optional
import yaml

from ..audit.event_collector import AuditEventCollector
from ..runtime.orchestrator import Orchestrator
from ..schemas.agent import AgentNodeConfig, AgentRole
from ..schemas.workflow import WorkflowConfig, WorkflowEdge
from .baseline import BaselineTrialExecutor
from .metrics import (
    CSSCalculator,
    PerformanceMetricsCalculator,
    SecurityMetricsCalculator,
    TUECalculator,
)
from .protected import ProtectedTrialExecutor


class EvaluationRunner:
    """Orchestrates repeatable scenario benchmarking across baseline and protected modes."""

    def __init__(
        self,
        orchestrator: Optional[Orchestrator] = None,
        event_collector: Optional[AuditEventCollector] = None,
        scenarios_dir: Optional[str] = None,
    ):
        self.collector = event_collector or AuditEventCollector()
        self.orchestrator = orchestrator or Orchestrator(event_collector=self.collector)
        self.baseline_executor = BaselineTrialExecutor(self.orchestrator)
        self.protected_executor = ProtectedTrialExecutor(self.orchestrator)
        self.css_calc = CSSCalculator()
        self.tue_calc = TUECalculator()
        self.sec_calc = SecurityMetricsCalculator()
        self.perf_calc = PerformanceMetricsCalculator()
        self.scenarios_dir = scenarios_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "scenarios")
        )

    def load_scenarios(self) -> List[Dict[str, Any]]:
        """Load all versioned YAML scenario specifications."""
        scenarios: List[Dict[str, Any]] = []
        pattern = os.path.join(self.scenarios_dir, "**", "*.yaml")
        yaml_files = glob.glob(pattern, recursive=True)

        for path in yaml_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    sc = yaml.safe_load(f)
                    if sc and isinstance(sc, dict) and "id" in sc:
                        scenarios.append(sc)
            except Exception as e:
                print(f"Error loading scenario {path}: {e}")

        return sorted(scenarios, key=lambda s: s["id"])

    def create_default_workflow(self) -> WorkflowConfig:
        """Create standard 3-agent software engineering test workflow."""
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
            workflow_id="eval_se_workflow_001",
            name="Evaluation Multi-Agent Workflow",
            entry_node_id="backend_agent",
            nodes=[backend_node, db_node, qa_node],
            edges=[
                WorkflowEdge(source_node_id="backend_agent", target_node_id="db_manager_agent"),
                WorkflowEdge(source_node_id="db_manager_agent", target_node_id="qa_agent"),
            ],
        )

    async def run_evaluation_suite(
        self, scenarios: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Run all loaded scenarios under both baseline and protected conditions."""
        sc_list = scenarios if scenarios is not None else self.load_scenarios()
        workflow = self.create_default_workflow()

        baseline_trials: List[Dict[str, Any]] = []
        protected_trials: List[Dict[str, Any]] = []

        for sc in sc_list:
            # 1. Run baseline trial
            b_res = await self.baseline_executor.execute_trial(sc, workflow)
            baseline_trials.append(b_res)

            # 2. Run protected trial
            p_res = await self.protected_executor.execute_trial(sc, workflow)
            protected_trials.append(p_res)

        # Aggregate Statistics
        total_adversarial = len([s for s in sc_list if s.get("ground_truth_label") == "adversarial"])
        total_benign = len([s for s in sc_list if s.get("ground_truth_label") == "benign"])

        # Baseline security metrics
        b_successful_attacks = len([t for t in baseline_trials if t["adversarial_objective_achieved"]])
        b_asr = self.sec_calc.calculate_asr(total_adversarial, b_successful_attacks)

        # Protected security metrics
        p_successful_attacks = len([t for t in protected_trials if t["adversarial_objective_achieved"]])
        p_asr = self.sec_calc.calculate_asr(total_adversarial, p_successful_attacks)

        # False positives (benign scenarios where an action was falsely blocked)
        p_false_blocks = len(
            [t for t in protected_trials if t["ground_truth_label"] == "benign" and t["blocked_actions"] > 0]
        )
        p_fpr = self.sec_calc.calculate_fpr(total_benign, p_false_blocks)

        # Latency calculations
        b_latencies = [t["duration_ms"] for t in baseline_trials]
        p_latencies = [t["duration_ms"] for t in protected_trials]
        b_perf = self.perf_calc.calculate_latency_distribution(b_latencies)
        p_perf = self.perf_calc.calculate_latency_distribution(p_latencies)
        overhead = self.perf_calc.calculate_overhead(b_perf["mean"], p_perf["mean"])

        return {
            "total_scenarios": len(sc_list),
            "adversarial_scenarios": total_adversarial,
            "benign_scenarios": total_benign,
            "baseline": {
                "asr": b_asr.model_dump(),
                "performance": b_perf,
                "trials": baseline_trials,
            },
            "protected": {
                "asr": p_asr.model_dump(),
                "fpr": p_fpr.model_dump(),
                "performance": p_perf,
                "trials": protected_trials,
            },
            "overhead": overhead.model_dump(),
        }
