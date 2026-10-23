"""Performance and latency distribution evaluation metrics."""

import math
from typing import Dict, List, Optional
from ...schemas.metrics import MetricResult


class PerformanceMetricsCalculator:
    """Calculates latency distribution (p50, p90, p99, mean) and overhead."""

    def calculate_latency_distribution(self, latencies_ms: List[float]) -> Dict[str, float]:
        """Compute p50, p90, p99, mean, min, and max latency."""
        if not latencies_ms:
            return {"p50": 0.0, "p90": 0.0, "p99": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}

        sorted_lat = sorted(latencies_ms)
        n = len(sorted_lat)

        def percentile(p: float) -> float:
            k = (n - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return sorted_lat[int(k)]
            d0 = sorted_lat[int(f)] * (c - k)
            d1 = sorted_lat[int(c)] * (k - f)
            return round(d0 + d1, 2)

        return {
            "p50": percentile(0.50),
            "p90": percentile(0.90),
            "p99": percentile(0.99),
            "mean": round(sum(sorted_lat) / n, 2),
            "min": round(sorted_lat[0], 2),
            "max": round(sorted_lat[-1], 2),
        }

    def calculate_overhead(
        self, baseline_avg_ms: float, protected_avg_ms: float
    ) -> MetricResult:
        """Calculate added mediation overhead in milliseconds and percentage."""
        overhead_ms = round(protected_avg_ms - baseline_avg_ms, 2)
        pct = (
            round((overhead_ms / baseline_avg_ms) * 100.0, 2)
            if baseline_avg_ms > 0
            else 0.0
        )

        return MetricResult(
            name="Runtime Mediation Overhead",
            value=overhead_ms,
            available=True,
            metadata={
                "baseline_avg_ms": baseline_avg_ms,
                "protected_avg_ms": protected_avg_ms,
                "overhead_percentage": pct,
                "unit": "milliseconds",
            },
        )
