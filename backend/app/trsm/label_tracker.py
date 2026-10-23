"""Trust label tracker and provenance security utilities."""

from typing import List, Set
from ..schemas.provenance import ProvenanceRecord, TrustLabel


class LabelTracker:
    """Manages label lifecycle and enforces non-elevation security invariants."""

    # Labels considered untrusted/tainted
    UNTRUSTED_LABELS: Set[TrustLabel] = {
        TrustLabel.UNTRUSTED_EXTERNAL,
        TrustLabel.USER_INPUT,
    }

    # Labels that require explicit validation to grant
    PRIVILEGED_LABELS: Set[TrustLabel] = {
        TrustLabel.TRUSTED_POLICY,
        TrustLabel.VALIDATED,
    }

    def can_transition_to(
        self, current_labels: List[TrustLabel], target_label: TrustLabel, is_validator_node: bool = False
    ) -> bool:
        """Enforces that untrusted data cannot transition to trusted without authorized validator."""
        current_set = set(current_labels)

        # If data is tainted with UNTRUSTED_EXTERNAL
        if TrustLabel.UNTRUSTED_EXTERNAL in current_set:
            if target_label in self.PRIVILEGED_LABELS and not is_validator_node:
                return False

        return True

    def merge_provenance(
        self, records: List[ProvenanceRecord], new_node_id: str, new_event_id: str
    ) -> ProvenanceRecord:
        """Merge provenance from multiple inputs (e.g. multi-agent join)."""
        if not records:
            return ProvenanceRecord(
                origin_type=TrustLabel.AGENT_GENERATED,
                source_event_ids=[new_event_id],
                trust_labels=[TrustLabel.AGENT_GENERATED],
                lineage_path=[new_node_id],
            )

        merged_labels: Set[TrustLabel] = {TrustLabel.AGENT_GENERATED}
        merged_source_events: List[str] = [new_event_id]
        deepest_lineage: List[str] = []

        # Taint propagation: if any input was untrusted, the merged record remains untrusted
        has_untrusted = False
        primary_origin = records[0].origin_type

        for r in records:
            merged_labels.update(r.trust_labels)
            merged_source_events.extend(r.source_event_ids)
            if len(r.lineage_path) > len(deepest_lineage):
                deepest_lineage = r.lineage_path
            if TrustLabel.UNTRUSTED_EXTERNAL in r.trust_labels:
                has_untrusted = True
                primary_origin = TrustLabel.UNTRUSTED_EXTERNAL

        if has_untrusted:
            merged_labels.add(TrustLabel.UNTRUSTED_EXTERNAL)
            # Remove silently elevated validated tag if present from mixed source
            merged_labels.discard(TrustLabel.VALIDATED)

        return ProvenanceRecord(
            origin_type=primary_origin,
            source_event_ids=list(set(merged_source_events)),
            trust_labels=list(merged_labels),
            lineage_path=deepest_lineage + [new_node_id],
        )
