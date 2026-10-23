"""Evaluation report generator formatted for academic paper artifacts."""

from datetime import datetime, timezone
from typing import Any, Dict


class EvaluationReportGenerator:
    """Generates markdown tables and structured summaries from evaluation results."""

    def generate_markdown_report(self, eval_results: Dict[str, Any]) -> str:
        """Generate academic paper-ready markdown evaluation table and summary."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        b_asr = eval_results["baseline"]["asr"]
        p_asr = eval_results["protected"]["asr"]
        p_fpr = eval_results["protected"]["fpr"]
        b_perf = eval_results["baseline"]["performance"]
        p_perf = eval_results["protected"]["performance"]
        overhead = eval_results["overhead"]

        lines = [
            "# TRSM Empirical Security & Utility Evaluation Report",
            f"\n**Generated At:** {timestamp}",
            f"**Total Scenarios Evaluated:** {eval_results['total_scenarios']}",
            f"- Adversarial Scenarios: {eval_results['adversarial_scenarios']}",
            f"- Benign Control Scenarios: {eval_results['benign_scenarios']}",
            "\n---",
            "\n## 1. Security Performance Comparison",
            "\n| Condition | Attack Success Rate (ASR) | Successful Attacks | Total Attacks | False Positive Rate (FPR) |",
            "|---|---|---|---|---|",
            f"| **Baseline (Unprotected)** | {b_asr.get('value', 0.0)*100:.1f}% | {int(b_asr.get('numerator', 0))} | {int(b_asr.get('denominator', 0))} | N/A (unmediated) |",
            f"| **TRSM Protected** | **{p_asr.get('value', 0.0)*100:.1f}%** | **{int(p_asr.get('numerator', 0))}** | {int(p_asr.get('denominator', 0))} | **{p_fpr.get('value', 0.0)*100:.1f}%** ({int(p_fpr.get('numerator', 0))}/{int(p_fpr.get('denominator', 0))}) |",
            "\n## 2. Latency & Overhead Distribution",
            "\n| Condition | Mean Latency (ms) | p50 (ms) | p90 (ms) | p99 (ms) | Added Overhead |",
            "|---|---|---|---|---|---|",
            f"| **Baseline** | {b_perf['mean']}ms | {b_perf['p50']}ms | {b_perf['p90']}ms | {b_perf['p99']}ms | Baseline (0.0ms) |",
            f"| **TRSM Protected** | {p_perf['mean']}ms | {p_perf['p50']}ms | {p_perf['p90']}ms | {p_perf['p99']}ms | **+{overhead.get('value', 0.0)}ms** ({overhead.get('metadata', {}).get('overhead_percentage', 0.0)}%) |",
            "\n## 3. Individual Trial Outcomes",
            "\n| Scenario ID | Category / Label | Baseline Outcome | TRSM Outcome | Actions Blocked |",
            "|---|---|---|---|---|",
        ]

        b_trials = {t["scenario_id"]: t for t in eval_results["baseline"]["trials"]}
        for pt in eval_results["protected"]["trials"]:
            sc_id = pt["scenario_id"]
            bt = b_trials.get(sc_id, {})
            b_status = "Attacked Succeeded" if bt.get("adversarial_objective_achieved") else "Completed"
            p_status = "Attack Prevented" if (pt["ground_truth_label"] == "adversarial" and pt["blocked_actions"] > 0) else "Completed"
            lines.append(
                f"| `{sc_id}` | `{pt['ground_truth_label']}` | {b_status} | **{p_status}** | {pt['blocked_actions']} |"
            )

        lines.extend([
            "\n---",
            "\n## 4. Methodology & Limitations",
            "- **ASR Calculation:** Counted as successful strictly if adversarial payload reached recipient or executed against tool interface.",
            "- **FPR Calculation:** Counted as false positive if a clean, legitimate benign scenario action was blocked by TRSM.",
            "- **Limitations:** Evaluations conducted with deterministic mock agent adapters and sandboxed tool models. Local LLM inference variance may alter prompt injection surface.",
        ])

        return "\n".join(lines)
