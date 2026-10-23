import React from 'react';
import { RunMetrics } from '../../types';
import { Activity, Gauge, ShieldAlert, Cpu } from 'lucide-react';

interface MetricsPanelProps {
  metrics: RunMetrics | null;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ metrics }) => {
  if (!metrics) {
    return (
      <div className="glass-panel" style={{ padding: '18px', textAlign: 'center', color: '#64748b' }}>
        No evaluation metrics calculated for current run.
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ padding: '18px' }}>
      <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '14px' }}>
        Security & Synergy Metrics
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px' }}>
        <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(30, 41, 59, 0.6)', border: '1px solid #334155' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#818cf8', marginBottom: '6px' }}>
            <Activity size={14} />
            <span style={{ fontSize: '11px', fontWeight: 600 }}>CSS Score</span>
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc' }}>
            {metrics.css.available ? `${((metrics.css.value || 0) * 100).toFixed(1)}%` : 'N/A'}
          </div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>Component Synergy</div>
        </div>

        <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(30, 41, 59, 0.6)', border: '1px solid #334155' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8', marginBottom: '6px' }}>
            <Gauge size={14} />
            <span style={{ fontSize: '11px', fontWeight: 600 }}>TUE Score</span>
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc' }}>
            {metrics.tue.available ? `${((metrics.tue.value || 0) * 100).toFixed(1)}%` : 'N/A'}
          </div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>Tool Efficacy</div>
        </div>

        <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(30, 41, 59, 0.6)', border: '1px solid #334155' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444', marginBottom: '6px' }}>
            <ShieldAlert size={14} />
            <span style={{ fontSize: '11px', fontWeight: 600 }}>Blocked Attacks</span>
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#ef4444' }}>
            {metrics.security_blocked_attacks}
          </div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>Threats Neutralized</div>
        </div>

        <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(30, 41, 59, 0.6)', border: '1px solid #334155' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981', marginBottom: '6px' }}>
            <Cpu size={14} />
            <span style={{ fontSize: '11px', fontWeight: 600 }}>Avg Latency</span>
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc' }}>
            {metrics.avg_latency_ms.toFixed(1)}ms
          </div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>Mediation Overhead</div>
        </div>
      </div>
    </div>
  );
};
