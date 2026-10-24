import React, { useState } from 'react';
import { ShieldAlert, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { reviewsApi, ReviewRecord } from '../../api/reviews';

interface ReviewModalProps {
  review: ReviewRecord | null;
  isOpen: boolean;
  onClose: () => void;
  onResolved: (reviewId: string, decision: 'ALLOW' | 'BLOCK') => void;
}

export const ReviewModal: React.FC<ReviewModalProps> = ({
  review,
  isOpen,
  onClose,
  onResolved,
}) => {
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !review) return null;

  const handleDecision = async (decision: 'ALLOW' | 'BLOCK') => {
    setIsSubmitting(true);
    try {
      await reviewsApi.resolve(review.review_id, decision, comment || `Decision ${decision} by operator`);
      onResolved(review.review_id, decision);
      onClose();
    } catch (err) {
      console.error('Failed to resolve review:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '500px',
          maxWidth: '100%',
          background: 'linear-gradient(135deg, rgba(24, 18, 43, 0.98) 0%, rgba(15, 23, 42, 0.98) 100%)',
          border: '1px solid rgba(139, 92, 246, 0.5)',
          boxShadow: '0 0 40px rgba(139, 92, 246, 0.3)',
          padding: '24px',
          borderRadius: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div
            style={{
              padding: '10px',
              borderRadius: '12px',
              background: 'rgba(139, 92, 246, 0.25)',
              color: '#a78bfa',
            }}
          >
            <ShieldAlert size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '17px', fontWeight: 700, color: '#f8fafc' }}>
              Human Authorization Required
            </h3>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>
              High-Risk Operation Intercepted by TRSM Policy
            </span>
          </div>
        </div>

        <div style={{ background: 'rgba(30, 41, 59, 0.6)', padding: '14px', borderRadius: '8px', marginBottom: '16px', fontSize: '12px', color: '#cbd5e1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ color: '#64748b' }}>Action Type:</span>
            <span style={{ fontFamily: 'monospace', color: '#f59e0b', fontWeight: 600 }}>{review.action_type}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ color: '#64748b' }}>Requesting Agent:</span>
            <span style={{ fontWeight: 600 }}>{review.actor_id}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#64748b' }}>Target Resource:</span>
            <span style={{ fontWeight: 600 }}>{review.target}</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#f59e0b', marginBottom: '16px' }}>
          <AlertTriangle size={15} />
          <span>This action cannot proceed until an operator approves or denies it.</span>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', display: 'block', marginBottom: '6px' }}>
            Reviewer Notes / Authorization Rationale
          </label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="e.g. Verified production staging checklist and approved release..."
            rows={3}
            style={{
              width: '100%',
              padding: '10px',
              borderRadius: '8px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid #475569',
              color: '#f8fafc',
              fontSize: '12px',
              resize: 'none',
            }}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button
            onClick={() => handleDecision('BLOCK')}
            disabled={isSubmitting}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '9px 16px',
              borderRadius: '8px',
              background: 'rgba(244, 63, 94, 0.2)',
              border: '1px solid #f43f5e',
              color: '#f43f5e',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <XCircle size={16} />
            <span>Deny & Block</span>
          </button>

          <button
            onClick={() => handleDecision('ALLOW')}
            disabled={isSubmitting}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '9px 18px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
              border: 'none',
              color: '#ffffff',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 0 15px rgba(16, 185, 129, 0.4)',
            }}
          >
            <CheckCircle2 size={16} />
            <span>Authorize Operation</span>
          </button>
        </div>
      </div>
    </div>
  );
};
