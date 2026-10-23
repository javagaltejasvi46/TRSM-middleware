import React, { useState } from 'react';
import { PlaygroundPage } from './pages/PlaygroundPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { Shield, LayoutGrid, BarChart2 } from 'lucide-react';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'playground' | 'evaluation'>('playground');

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navigation Bar */}
      <nav
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 24px',
          background: 'rgba(15, 23, 42, 0.95)',
          borderBottom: '1px solid #334155',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              padding: '6px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
              color: '#ffffff',
            }}
          >
            <Shield size={20} />
          </div>
          <span style={{ fontWeight: 700, fontSize: '16px', letterSpacing: '-0.02em', color: '#f8fafc' }}>
            TRSM Middleware
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setCurrentPage('playground')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 500,
              cursor: 'pointer',
              background: currentPage === 'playground' ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
              color: currentPage === 'playground' ? '#818cf8' : '#94a3b8',
              border: `1px solid ${currentPage === 'playground' ? '#818cf8' : 'transparent'}`,
            }}
          >
            <LayoutGrid size={15} />
            <span>Playground</span>
          </button>

          <button
            onClick={() => setCurrentPage('evaluation')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 500,
              cursor: 'pointer',
              background: currentPage === 'evaluation' ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
              color: currentPage === 'evaluation' ? '#818cf8' : '#94a3b8',
              border: `1px solid ${currentPage === 'evaluation' ? '#818cf8' : 'transparent'}`,
            }}
          >
            <BarChart2 size={15} />
            <span>Evaluation</span>
          </button>
        </div>
      </nav>

      {/* Page Content */}
      <main style={{ flex: 1 }}>
        {currentPage === 'playground' ? <PlaygroundPage /> : <EvaluationPage />}
      </main>
    </div>
  );
};

export default App;
