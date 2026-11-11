import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NodeConfigPanel } from './NodeConfigPanel';
import { defaultWorkflow } from '../../lib/workflowGraph';
import { AgentNodeConfig } from '../../types';

const backend = defaultWorkflow().nodes[0];

function setup(overrides: Partial<Pick<React.ComponentProps<typeof NodeConfigPanel>, 'node' | 'otherNodeIds' | 'isEntry'>> = {}) {
  const props = {
    node: backend,
    otherNodeIds: ['db_manager_agent', 'qa_agent'],
    isEntry: true,
    ...overrides,
    onApply: vi.fn<(next: AgentNodeConfig) => void>(),
    onDelete: vi.fn<() => void>(),
    onSetEntry: vi.fn<() => void>(),
  };
  render(<NodeConfigPanel {...props} />);
  return { props, user: userEvent.setup() };
}

describe('NodeConfigPanel', () => {
  it('shows the current configuration with labelled fields', () => {
    setup();
    expect(screen.getByLabelText('Node ID')).toHaveValue('backend_agent');
    expect(screen.getByLabelText('Display name')).toHaveValue('Backend Agent');
    expect(screen.getByLabelText('Role')).toHaveValue('backend');
    expect(screen.getByLabelText('Timeout (s)')).toHaveValue('30');
    expect(screen.getByRole('checkbox', { name: 'db_manager_agent' })).toBeChecked();
    expect(screen.getByRole('checkbox', { name: 'qa_agent' })).not.toBeChecked();
    expect(screen.getByRole('button', { name: 'Apply' })).toBeDisabled();
  });

  it('shows an inline error linked to an out-of-range field and blocks Apply', async () => {
    const { user, props } = setup();
    const timeout = screen.getByLabelText('Timeout (s)');
    await user.clear(timeout);
    await user.type(timeout, '301');
    expect(timeout).toHaveAttribute('aria-invalid', 'true');
    expect(timeout).toHaveAccessibleDescription(/whole number from 1 to 300/);
    expect(screen.getByRole('button', { name: 'Apply' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Apply' }));
    expect(props.onApply).not.toHaveBeenCalled();
  });

  it('rejects a node ID already used by another node', async () => {
    const { user } = setup();
    const id = screen.getByLabelText('Node ID');
    await user.clear(id);
    await user.type(id, 'qa_agent');
    expect(id).toHaveAccessibleDescription(/Another node already uses "qa_agent"/);
    expect(screen.getByRole('button', { name: 'Apply' })).toBeDisabled();
  });

  it('applies edits with parsed numbers, peers and tools', async () => {
    const { user, props } = setup();
    await user.click(screen.getByRole('checkbox', { name: 'qa_agent' }));
    await user.click(screen.getByRole('checkbox', { name: 'db_manager_agent' }));
    await user.clear(screen.getByLabelText('Call limit'));
    await user.type(screen.getByLabelText('Call limit'), '25');
    await user.type(screen.getByLabelText('Allowed tools'), 'test_suite{Enter}');
    await user.click(screen.getByRole('button', { name: 'Apply' }));
    expect(props.onApply).toHaveBeenCalledTimes(1);
    expect(props.onApply.mock.calls[0][0]).toMatchObject({
      node_id: 'backend_agent',
      allowed_peers: ['qa_agent'],
      allowed_tools: ['customer_db', 'test_suite'],
      call_limit: 25,
      timeout_seconds: 30,
    });
  });

  it('marks unregistered tools and lets peers outside the workflow be removed', async () => {
    const { user, props } = setup({ node: { ...backend, allowed_peers: ['ghost'], allowed_tools: ['shell_exec'] } });
    expect(screen.getByText('(unregistered)')).toBeInTheDocument();
    expect(screen.getByText(/"ghost" is not in this workflow/)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Remove peer ghost' }));
    await user.click(screen.getByRole('button', { name: 'Apply' }));
    expect(props.onApply.mock.calls[0][0].allowed_peers).toEqual([]);
  });

  it('Reset discards the draft; Delete and Set as entry call back', async () => {
    const { user, props } = setup({ isEntry: false });
    await user.type(screen.getByLabelText('Display name'), ' X');
    await user.click(screen.getByRole('button', { name: 'Reset' }));
    expect(screen.getByLabelText('Display name')).toHaveValue('Backend Agent');
    await user.click(screen.getByRole('button', { name: /Set as entry/ }));
    await user.click(screen.getByRole('button', { name: /Delete node/ }));
    expect(props.onSetEntry).toHaveBeenCalledTimes(1);
    expect(props.onDelete).toHaveBeenCalledTimes(1);
  });
});
