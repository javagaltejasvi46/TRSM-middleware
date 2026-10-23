"""Provenance tracking and lineage management."""

from typing import List, Optional
from ..schemas.provenance import ProvenanceRecord, TrustLabel


class ProvenanceTracker:
    """Tracks origin, lineage hops, and trust labels across agent executions."""

    def create_initial_record(
        self, origin_type: TrustLabel = TrustLabel.USER_INPUT, initial_node: str = "user"
    ) -> ProvenanceRecord:
        """Create a fresh root provenance record."""
        return ProvenanceRecord(
            origin_type=origin_type,
            trust_labels=[origin_type],
            lineage_path=[initial_node],
        )

    def advance_lineage(
        self,
        current_record: Optional[ProvenanceRecord],
        current_node_id: str,
        source_event_id: str,
        new_label: TrustLabel = TrustLabel.AGENT_GENERATED,
    ) -> ProvenanceRecord:
        """Advance lineage path without elevating untrusted labels."""
        if not current_record:
            return ProvenanceRecord(
                origin_type=new_label,
                source_event_ids=[source_event_id],
                trust_labels=[new_label],
                lineage_path=[current_node_id],
            )

        labels = set(current_record.trust_labels)
        labels.add(new_label)

        # Do NOT elevate untrusted_external if present
        return ProvenanceRecord(
            origin_type=current_record.origin_type,
            source_event_ids=[source_event_id],
            trust_labels=list(labels),
            lineage_path=current_record.lineage_path + [current_node_id],
        )
