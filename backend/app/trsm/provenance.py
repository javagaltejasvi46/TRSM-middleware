"""Provenance tracking and lineage management with non-elevation guarantees."""

from typing import List, Optional, Set
from ..schemas.provenance import ProvenanceRecord, TrustLabel
from .label_tracker import LabelTracker


class ProvenanceTracker:
    """Tracks origin, lineage hops, and trust labels across agent executions."""

    def __init__(self):
        self.label_tracker = LabelTracker()

    def create_initial_record(
        self,
        origin_type: TrustLabel = TrustLabel.USER_INPUT,
        initial_node: str = "user",
        source_event_id: Optional[str] = None,
    ) -> ProvenanceRecord:
        """Create a fresh root provenance record."""
        return ProvenanceRecord(
            origin_type=origin_type,
            source_event_ids=[source_event_id] if source_event_id else [],
            trust_labels=[origin_type],
            lineage_path=[initial_node],
        )

    def advance_lineage(
        self,
        current_record: Optional[ProvenanceRecord],
        current_node_id: str,
        source_event_id: str,
        new_label: TrustLabel = TrustLabel.AGENT_GENERATED,
        is_validator: bool = False,
    ) -> ProvenanceRecord:
        """Advance lineage path without elevating untrusted labels."""
        if not current_record:
            return ProvenanceRecord(
                origin_type=new_label,
                source_event_ids=[source_event_id],
                trust_labels=[new_label],
                lineage_path=[current_node_id],
            )

        labels: Set[TrustLabel] = set(current_record.trust_labels)

        # Enforce non-elevation invariant:
        # If origin was UNTRUSTED_EXTERNAL, an agent repeating or summarizing it
        # retains UNTRUSTED_EXTERNAL taint unless explicitly marked by validator
        if current_record.origin_type == TrustLabel.UNTRUSTED_EXTERNAL:
            labels.add(TrustLabel.UNTRUSTED_EXTERNAL)
            if new_label == TrustLabel.VALIDATED and not is_validator:
                # Reject invalid elevation attempt
                pass
            else:
                labels.add(new_label)
        else:
            labels.add(new_label)

        return ProvenanceRecord(
            origin_type=current_record.origin_type,
            source_event_ids=[source_event_id],
            trust_labels=list(labels),
            lineage_path=current_record.lineage_path + [current_node_id],
        )

    def is_tainted(self, record: Optional[ProvenanceRecord]) -> bool:
        """Check if record originates from or contains untrusted external input."""
        if not record:
            return False
        return (
            record.origin_type == TrustLabel.UNTRUSTED_EXTERNAL
            or TrustLabel.UNTRUSTED_EXTERNAL in record.trust_labels
        )
