import React from 'react';
import { RunMetrics } from '../../types';
import { Activity, Gauge, ShieldAlert, Cpu } from 'lucide-react';

interface MetricsPanelProps {
  metrics: RunMetrics | null;
}

const Tile: React.FC<{ Icon: React.ElementType; label: string; value: string; caption: string; color: string }> = ({ Icon, label, value, caption, color }) => (
  <div className="well" style={{ padding: '12px 14px', background: 'linear-gradient(180deg, #ffffff 0%, var(--surface-sunken) 100%)', boxShadow: 'inset 0 1px 0 #ffffff, 0 2px 6px rgba(30, 27, 75, 0.05)' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color, marginBottom: '6px' }}>
      <Icon size={14} aria-hidden="true" />
      <span style={{ fontSize: '12px', fontWeight: 600 }}>{label}</span>
    </div>
    <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>{value}</div>
    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{caption}</div>
  </div>
);

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ metrics }) => {
  if (!metrics) {
    return (
      <div className="surface" style={{ padding: '18px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '13px' }}>
        No metrics yet. They are calculated by the backend after a run.
      </div>
    );
  }

  const pct = (m: RunMetrics['css']) => (m.available ? `${((m.value || 0) * 100).toFixed(1)}%` : 'Not available');

  return (
    <div className="surface" style={{ padding: '16px' }}>
      <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '12px' }}>Security & Synergy Metrics (this run)</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px' }}>
        <Tile Icon={Activity} label="CSS Score" value={pct(metrics.css)} caption="Component Synergy" color="var(--accent-text)" />
        <Tile Icon={Gauge} label="TUE Score" value={pct(metrics.tue)} caption="Tool Efficacy" color="var(--info-text)" />
        <Tile Icon={ShieldAlert} label="Blocked Attacks" value={String(metrics.security_blocked_attacks)} caption="Threats blocked" color="var(--status-block)" />
        <Tile Icon={Cpu} label="Avg Latency" value={`${metrics.avg_latency_ms.toFixed(1)} ms`} caption="Mediation overhead" color="var(--status-allow)" />
      </div>
    </div>
  );
};
