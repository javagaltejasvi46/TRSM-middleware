import React, { useState } from 'react';
import { PlaygroundPage } from './pages/PlaygroundPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { Shield, LayoutGrid, BarChart2 } from 'lucide-react';

type Page = 'playground' | 'evaluation';

const NAV: { id: Page; label: string; Icon: React.ElementType }[] = [
  { id: 'playground', label: 'Playground', Icon: LayoutGrid },
  { id: 'evaluation', label: 'Evaluation', Icon: BarChart2 },
];

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<Page>('playground');

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <nav
        aria-label="Main"
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 20,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '10px 24px',
          background: 'rgba(255, 255, 255, 0.78)',
          backdropFilter: 'blur(14px) saturate(160%)',
          WebkitBackdropFilter: 'blur(14px) saturate(160%)',
          borderBottom: '1px solid var(--border-color)',
          boxShadow: '0 1px 0 rgba(255, 255, 255, 0.9) inset, 0 4px 20px rgba(30, 27, 75, 0.06)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="icon-chip" style={{ color: '#ffffff', background: 'linear-gradient(180deg, #6366f1 0%, #4338ca 100%)', borderColor: '#4338ca' }}>
            <Shield size={18} aria-hidden="true" />
          </div>
          <span style={{ fontWeight: 700, fontSize: '16px', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>TRSM Middleware</span>
        </div>

        <div className="well" style={{ display: 'flex', gap: '4px', padding: '4px', borderRadius: '10px' }}>
          {NAV.map(({ id, label, Icon }) => {
            const active = currentPage === id;
            return (
              <button
                key={id}
                type="button"
                aria-current={active ? 'page' : undefined}
                onClick={() => setCurrentPage(id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  minHeight: '34px',
                  padding: '6px 14px',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: '1px solid',
                  borderColor: active ? 'var(--border-strong)' : 'transparent',
                  background: active ? '#ffffff' : 'transparent',
                  color: active ? 'var(--accent-text)' : 'var(--text-secondary)',
                  boxShadow: active ? 'inset 0 1px 0 #ffffff, 0 2px 6px rgba(30, 27, 75, 0.1)' : 'none',
                  transition: 'background-color 200ms ease, box-shadow 200ms ease, color 200ms ease',
                }}
              >
                <Icon size={15} aria-hidden="true" />
                <span>{label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      <main style={{ flex: 1 }}>{currentPage === 'playground' ? <PlaygroundPage /> : <EvaluationPage />}</main>
    </div>
  );
};

export default App;
