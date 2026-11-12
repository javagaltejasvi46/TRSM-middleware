import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { GatewayNode } from './GatewayNode';

describe('GatewayNode', () => {
  it('renders TRSM ON button when protected and triggers onToggleTrsm on click', async () => {
    const user = userEvent.setup();
    const onToggleTrsm = vi.fn();

    render(
      <GatewayNode
        id="__trsm_gateway__"
        type="gateway"
        data={{
          mediated: 5,
          blocked: 1,
          enableTrsm: true,
          onToggleTrsm,
        }}
        selected={false}
        selectable={false}
        deletable={false}
        draggable={false}
        zIndex={0}
        isConnectable={false}
        positionAbsoluteX={300}
        positionAbsoluteY={180}
        dragging={false}
      />,
    );

    expect(screen.getByText('TRSM Gateway')).toBeInTheDocument();
    const button = screen.getByRole('button', { name: /TRSM is ON/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('TRSM: ON');

    await user.click(button);
    expect(onToggleTrsm).toHaveBeenCalledTimes(1);
  });

  it('renders TRSM OFF button and baseline description when disabled', () => {
    render(
      <GatewayNode
        id="__trsm_gateway__"
        type="gateway"
        data={{
          mediated: null,
          blocked: null,
          enableTrsm: false,
          onToggleTrsm: vi.fn(),
        }}
        selected={false}
        selectable={false}
        deletable={false}
        draggable={false}
        zIndex={0}
        isConnectable={false}
        positionAbsoluteX={300}
        positionAbsoluteY={180}
        dragging={false}
      />,
    );

    const button = screen.getByRole('button', { name: /TRSM is OFF/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('TRSM: OFF');
    expect(screen.getByText(/TRSM enforcement is bypassed/i)).toBeInTheDocument();
  });
});
