"""Unit tests verifying multi-hop provenance and non-elevation security invariants."""

from app.schemas.provenance import TrustLabel
from app.trsm.label_tracker import LabelTracker
from app.trsm.provenance import ProvenanceTracker


def test_initial_provenance_creation():
    """Verify clean initial provenance record."""
    tracker = ProvenanceTracker()
    rec = tracker.create_initial_record(origin_type=TrustLabel.USER_INPUT, initial_node="user")
    assert rec.origin_type == TrustLabel.USER_INPUT
    assert rec.lineage_path == ["user"]
    assert TrustLabel.USER_INPUT in rec.trust_labels


def test_multi_hop_lineage_preservation():
    """Verify provenance lineage accumulates node hops across multiple agents."""
    tracker = ProvenanceTracker()
    # Hop 0: User input
    rec0 = tracker.create_initial_record(origin_type=TrustLabel.USER_INPUT, initial_node="user")

    # Hop 1: Backend Agent processes
    rec1 = tracker.advance_lineage(
        current_record=rec0,
        current_node_id="backend_agent",
        source_event_id="evt-1",
        new_label=TrustLabel.AGENT_GENERATED,
    )
    assert rec1.lineage_path == ["user", "backend_agent"]

    # Hop 2: DB Manager processes
    rec2 = tracker.advance_lineage(
        current_record=rec1,
        current_node_id="db_manager_agent",
        source_event_id="evt-2",
        new_label=TrustLabel.TOOL_RESULT,
    )
    assert rec2.lineage_path == ["user", "backend_agent", "db_manager_agent"]

    # Hop 3: QA Agent evaluates
    rec3 = tracker.advance_lineage(
        current_record=rec2,
        current_node_id="qa_agent",
        source_event_id="evt-3",
        new_label=TrustLabel.AGENT_GENERATED,
    )
    assert rec3.lineage_path == ["user", "backend_agent", "db_manager_agent", "qa_agent"]
    assert rec3.origin_type == TrustLabel.USER_INPUT


def test_untrusted_external_never_silently_elevated():
    """CRITICAL INVARIANT: Untrusted external data cannot be silently elevated to VALIDATED."""
    tracker = ProvenanceTracker()
    rec_external = tracker.create_initial_record(
        origin_type=TrustLabel.UNTRUSTED_EXTERNAL, initial_node="web_scraper"
    )
    assert tracker.is_tainted(rec_external) is True

    # Intermediate agent repeats or summarizes it without an authorized validator
    rec_summarized = tracker.advance_lineage(
        current_record=rec_external,
        current_node_id="backend_agent",
        source_event_id="evt-10",
        new_label=TrustLabel.VALIDATED,  # Attempting unauthorized elevation
        is_validator=False,
    )

    # Invariant holds: Taint remains, VALIDATED was NOT granted
    assert TrustLabel.UNTRUSTED_EXTERNAL in rec_summarized.trust_labels
    assert TrustLabel.VALIDATED not in rec_summarized.trust_labels
    assert tracker.is_tainted(rec_summarized) is True


def test_label_tracker_merge_preserves_taint():
    """Merging clean and untrusted branches retains untrusted taint."""
    tracker = LabelTracker()
    clean_rec = ProvenanceTracker().create_initial_record(
        origin_type=TrustLabel.TRUSTED_POLICY, initial_node="policy_store"
    )
    untrusted_rec = ProvenanceTracker().create_initial_record(
        origin_type=TrustLabel.UNTRUSTED_EXTERNAL, initial_node="external_feed"
    )

    merged = tracker.merge_provenance(
        records=[clean_rec, untrusted_rec],
        new_node_id="joining_agent",
        new_event_id="evt-join",
    )

    assert merged.origin_type == TrustLabel.UNTRUSTED_EXTERNAL
    assert TrustLabel.UNTRUSTED_EXTERNAL in merged.trust_labels
    assert "joining_agent" in merged.lineage_path
