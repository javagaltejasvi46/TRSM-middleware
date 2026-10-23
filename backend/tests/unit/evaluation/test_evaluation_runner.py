"""Unit tests for EvaluationRunner and ReportGenerator."""

import asyncio
from app.evaluation.report import EvaluationReportGenerator
from app.evaluation.runner import EvaluationRunner


def test_scenario_loader():
    """Verify evaluation runner loads versioned YAML scenarios."""
    runner = EvaluationRunner()
    scenarios = runner.load_scenarios()
    assert len(scenarios) >= 8

    # Ensure required fields are present in every scenario
    for sc in scenarios:
        assert "id" in sc
        assert "name" in sc
        assert "category" in sc
        assert "initial_task" in sc
        assert "expected_security_outcome" in sc
        assert "ground_truth_label" in sc


def test_evaluation_runner_and_report_generation():
    """Verify evaluation runner executes matched trials and formats report."""
    runner = EvaluationRunner()
    scenarios = runner.load_scenarios()

    async def _run():
        results = await runner.run_evaluation_suite(scenarios[:3])
        assert "baseline" in results
        assert "protected" in results
        assert results["total_scenarios"] == 3

        reporter = EvaluationReportGenerator()
        report_md = reporter.generate_markdown_report(results)
        assert "# TRSM Empirical Security & Utility Evaluation Report" in report_md
        assert "Attack Success Rate (ASR)" in report_md
        assert "Individual Trial Outcomes" in report_md

    asyncio.run(_run())
