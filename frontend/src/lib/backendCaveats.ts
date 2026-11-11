/**
 * Known gaps in what the backend reports, so the UI labels them instead of
 * displaying them as measurements. Remove an entry once the backend is fixed.
 * Verified against the code on 2026-11-11.
 */

/** RunMetrics fields that backend/app/services/evaluation_service.py fills with fixed constants. */
export const PLACEHOLDER_METRIC_FIELDS = {
  avg_latency_ms: 'fixed at 12.5 by evaluation_service.py; not measured',
  p95_latency_ms: 'fixed at 25.0 by evaluation_service.py; not measured',
  task_success: 'always true in evaluation_service.py; not evaluated',
} as const;

/** RunComparison.overhead_ms is avg_latency difference of two placeholders, so always 0. */
export const OVERHEAD_FIELD_NOTE = 'derived from the placeholder avg_latency_ms values, so it is always 0';

/** security_blocked_attacks counts every BLOCK/QUARANTINE event, so one blocked message counts twice. */
export const BLOCKED_ATTACKS_NOTE =
  'counts every audit event with a BLOCK/QUARANTINE decision (policy_decided and blocked), so one blocked message counts twice';

/** CSS/TUE report 1.0 ("100%") when nothing was proposed (denominator 0). */
export const ZERO_DENOMINATOR_NOTE = 'nothing was proposed (0/0); the backend reports 100% by convention';
