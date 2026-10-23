"""Unit tests for CSS, TUE, ASR, FPR, FNR, and performance metric calculations."""

from app.evaluation.metrics import (
    CSSCalculator,
    PerformanceMetricsCalculator,
    SecurityMetricsCalculator,
    TUECalculator,
)
from app.schemas.events import AuditEvent, AuditEventType
from app.schemas.policy import PolicyDecisionEnum


def test_css_calculation():
    """Verify CSS formula and edge cases."""
    calc = CSSCalculator()

    # Case 1: 0 messages proposed -> available with value 1.0
    res_zero = calc.calculate([])
    assert res_zero.value == 1.0
    assert res_zero.available is True

    # Case 2: 2 proposed, 2 delivered -> CSS = 1.0
    events = [
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a1", event_type=AuditEventType.MESSAGE_PROPOSED),
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a1", event_type=AuditEventType.MESSAGE_DELIVERED),
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a2", event_type=AuditEventType.MESSAGE_PROPOSED),
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a2", event_type=AuditEventType.MESSAGE_DELIVERED),
    ]
    res_full = calc.calculate(events)
    assert res_full.value == 1.0
    assert res_full.numerator == 2.0
    assert res_full.denominator == 2.0

    # Case 3: 2 proposed, 1 delivered, 1 blocked -> CSS = 0.5
    events_half = [
        AuditEvent(run_id="r2", trace_id="t2", actor_id="a1", event_type=AuditEventType.MESSAGE_PROPOSED),
        AuditEvent(run_id="r2", trace_id="t2", actor_id="a1", event_type=AuditEventType.MESSAGE_DELIVERED),
        AuditEvent(run_id="r2", trace_id="t2", actor_id="a2", event_type=AuditEventType.MESSAGE_PROPOSED),
        AuditEvent(run_id="r2", trace_id="t2", actor_id="a2", event_type=AuditEventType.MESSAGE_BLOCKED),
    ]
    res_half = calc.calculate(events_half)
    assert res_half.value == 0.5
    assert res_half.numerator == 1.0
    assert res_half.denominator == 2.0


def test_tue_calculation():
    """Verify Tool Utilization Efficacy formula and edge cases."""
    calc = TUECalculator()

    # Case 1: 0 tools proposed
    res_zero = calc.calculate([])
    assert res_zero.value == 1.0

    # Case 2: 4 tools proposed, 3 executed, 1 blocked -> TUE = 0.75
    events = [
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a1", event_type=AuditEventType.RESOURCE_PROPOSED),
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a1", event_type=AuditEventType.RESOURCE_EXECUTED),
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a1", event_type=AuditEventType.RESOURCE_PROPOSED),
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a1", event_type=AuditEventType.RESOURCE_EXECUTED),
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a1", event_type=AuditEventType.RESOURCE_PROPOSED),
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a1", event_type=AuditEventType.RESOURCE_EXECUTED),
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a1", event_type=AuditEventType.RESOURCE_PROPOSED),
        AuditEvent(run_id="r1", trace_id="t1", actor_id="a1", event_type=AuditEventType.RESOURCE_BLOCKED),
    ]
    res = calc.calculate(events)
    assert res.value == 0.75
    assert res.numerator == 3.0
    assert res.denominator == 4.0


def test_security_metrics_calculation():
    """Verify ASR, FPR, and FNR exact formulas and denominators."""
    calc = SecurityMetricsCalculator()

    # ASR: 10 attacks, 2 succeeded -> ASR = 0.20
    asr = calc.calculate_asr(total_attacks=10, successful_attacks=2)
    assert asr.value == 0.20
    assert asr.numerator == 2.0
    assert asr.denominator == 10.0

    # ASR with 0 attacks -> unavailable
    asr_empty = calc.calculate_asr(total_attacks=0, successful_attacks=0)
    assert asr_empty.available is False

    # FPR: 20 benign actions, 1 falsely blocked -> FPR = 0.05
    fpr = calc.calculate_fpr(total_benign=20, false_blocks=1)
    assert fpr.value == 0.05
    assert fpr.numerator == 1.0
    assert fpr.denominator == 20.0

    # FNR: 10 adversarial actions, 1 erroneously allowed -> FNR = 0.10
    fnr = calc.calculate_fnr(total_adversarial=10, missed_attacks=1)
    assert fnr.value == 0.10
    assert fnr.numerator == 1.0
    assert fnr.denominator == 10.0


def test_performance_percentiles_and_overhead():
    """Verify latency percentile distribution and overhead calculations."""
    calc = PerformanceMetricsCalculator()

    latencies = [10.0, 12.0, 14.0, 15.0, 18.0, 20.0, 25.0, 30.0, 50.0, 100.0]
    dist = calc.calculate_latency_distribution(latencies)
    assert dist["min"] == 10.0
    assert dist["max"] == 100.0
    assert dist["mean"] == 29.4
    assert dist["p50"] == 19.0

    overhead = calc.calculate_overhead(baseline_avg_ms=10.0, protected_avg_ms=12.5)
    assert overhead.value == 2.5
    assert overhead.metadata["overhead_percentage"] == 25.0
