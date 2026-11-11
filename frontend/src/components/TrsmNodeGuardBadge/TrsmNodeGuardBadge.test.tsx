import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TrsmNodeGuardBadge } from './TrsmNodeGuardBadge';

describe('TrsmNodeGuardBadge', () => {
  it('defaults to Idle when the backend has reported no status', () => {
    render(<TrsmNodeGuardBadge nodeId="qa_agent" />);
    expect(screen.getByRole('status', { name: 'TRSM Node Guard for qa_agent: Idle' })).toBeInTheDocument();
  });

  it.each([
    ['blocked', 'Blocked'],
    ['quarantined', 'Quarantined'],
    ['review_required', 'Awaiting review'],
  ] as const)('shows %s as text, not colour alone', (status, label) => {
    render(<TrsmNodeGuardBadge nodeId="qa_agent" status={status} />);
    expect(screen.getByText(label)).toBeVisible();
  });
});
