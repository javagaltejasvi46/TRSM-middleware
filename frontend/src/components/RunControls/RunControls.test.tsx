import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { RunControls } from './RunControls';

describe('RunControls', () => {
  it('renders execution controls with mode indicator and preloaded workflow menu', async () => {
    const user = userEvent.setup();
    const onSelectWorkflowId = vi.fn();
    const onStartRun = vi.fn();
    const onTaskChange = vi.fn();

    render(
      <RunControls
        isRunning={false}
        enableTrsm={true}
        task="Retrieve customer 1042 profile information."
        onTaskChange={onTaskChange}
        selectedWorkflowId="benign_se_pipeline"
        onSelectWorkflowId={onSelectWorkflowId}
        onStartRun={onStartRun}
      />,
    );

    // Title and mode indicator present (not a toggle button)
    expect(screen.getByText('Execution Controls')).toBeInTheDocument();
    expect(screen.getByText('TRSM Protected')).toBeInTheDocument();

    // Selectable preloaded workflow menu present
    const select = screen.getByLabelText(/Preloaded attack workflow/i);
    expect(select).toBeInTheDocument();

    await user.selectOptions(select, 'attack_prompt_injection');
    expect(onSelectWorkflowId).toHaveBeenCalledWith('attack_prompt_injection');

    // Execute run button fires with task and enableTrsm
    const executeBtn = screen.getByRole('button', { name: /Execute Run/i });
    await user.click(executeBtn);
    expect(onStartRun).toHaveBeenCalledWith('Retrieve customer 1042 profile information.', true);
  });
});
