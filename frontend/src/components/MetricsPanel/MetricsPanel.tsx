import React from 'react';
import { MetricResult, RunMetrics } from '../../types';
import { Activity, Gauge, ShieldAlert, Timer } from 'lucide-react';
import { BLOCKED_ATTACKS_NOTE, PLACEHOLDER_METRIC_FIELDS, ZERO_DENOMINATOR_NOTE } from '../../lib/backendCaveats';

interface MetricsPanelProps {
  metrics: RunMetrics | null;
}

const Tile: React.FC<{ Icon: React.ElementType; label: string; value: string; caption: string; color: string; muted?: boolean }> = ({ Icon, label, value, caption, color, muted }) => (
  <div className="well" style={{ padding: '12px 14px', background: 'linear-gradient(180deg, #ffffff 0%, var(--surface-sunken) 100%)', boxShadow: 'inset 0 1px 0 #ffffff, 0 2px 6px rgba(30, 27, 75, 0.05)' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color, marginBottom: '6px' }}>
      <Icon size={14} aria-hidden="true" />
      <span style={{ fontSize: '12px', fontWeight: 600 }}>{label}</span>
    </div>
    <div style={{ fontSize: muted ? '15px' : '22px', fontWeight: 700, color: muted ? 'var(--text-secondary)' : 'var(--text-primary)', letterSpacing: '-0.02em' }}>{value}</div>
    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{caption}</div>
  </div>
);

/** Value with its numerator/denominator, or an explicit reason when there is nothing to measure. */
const ratioMetric = (m: MetricResult, what: string): { value: string; caption: string; muted: boolean } => {
  if (!m.available) return { value: 'Not available', caption: m.unavailable_reason ?? what, muted: true };
  if (m.denominator === 0) return { value: 'n/a', caption: ZERO_DENOMINATOR_NOTE, muted: true };
  const pct = m.value == null ? '—' : `${(m.value * 100).toFixed(1)}%`;
  return { value: pct, caption: m.numerator != null && m.denominator != null ? `${m.numerator} of ${m.denominator} ${what}` : what, muted: false };
};

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ metrics }) => {
  if (!metrics) {
    return (
      <div className="surface" style={{ padding: '18px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '13px' }}>
        No metrics yet. They are calculated by the backend after a run.
      </div>
    );
  }

  const css = ratioMetric(metrics.css, 'messages delivered');
  const tue = ratioMetric(metrics.tue, 'tool actions executed');

  return (
    <div className="surface" style={{ padding: '16px' }}>
      <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '12px' }}>Security & Synergy Metrics (this run)</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '12px' }}>
        <Tile Icon={Activity} label="CSS Score" value={css.value} caption={css.caption} color="var(--accent-text)" muted={css.muted} />
        <Tile Icon={Gauge} label="TUE Score" value={tue.value} caption={tue.caption} color="var(--info-text)" muted={tue.muted} />
        <Tile
          Icon={ShieldAlert}
          label="Non-ALLOW decision events"
          value={String(metrics.security_blocked_attacks)}
          caption={`security_blocked_attacks: ${BLOCKED_ATTACKS_NOTE}`}
          color="var(--status-block)"
        />
        <Tile Icon={Timer} label="Latency" value="Not available" caption={`Backend value is ${PLACEHOLDER_METRIC_FIELDS.avg_latency_ms}. See Run status for measured duration.`} color="var(--text-secondary)" muted />
      </div>
    </div>
  );
};
