#!/usr/bin/env python3
"""CLI evaluation script to run baseline vs protected trials and output academic report."""

import argparse
import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.evaluation.report import EvaluationReportGenerator
from app.evaluation.runner import EvaluationRunner


async def main():
    parser = argparse.ArgumentParser(description="TRSM Empirical Evaluation Runner")
    parser.add_argument(
        "--output",
        default="artifacts/evaluation_report.md",
        help="Path to save generated markdown evaluation report",
    )
    args = parser.parse_args()

    print("=================================================================")
    print("TRSM EMPIRICAL BENCHMARK & EVALUATION RUNNER")
    print("=================================================================\n")

    runner = EvaluationRunner()
    scenarios = runner.load_scenarios()
    print(f"Loaded {len(scenarios)} versioned evaluation scenarios.")

    print("Executing matched baseline and protected trials...")
    results = await runner.run_evaluation_suite(scenarios)

    reporter = EvaluationReportGenerator()
    report_md = reporter.generate_markdown_report(results)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\nEvaluation Report Successfully Generated at: {args.output}\n")
    print("=================================================================")
    print(report_md)
    print("=================================================================")


if __name__ == "__main__":
    asyncio.run(main())
