import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TraceExplorer } from './TraceExplorer';
import { AuditEvent } from '../../types';

const ev = (id: string, over: Partial<AuditEvent> = {}): AuditEvent => ({
  event_id: id,
  run_id: 'run-1',
  trace_id: 'trace-1',
  timestamp: '2026-11-11T10:00:00.000Z',
  actor_id: 'backend_agent',
  event_type: 'message.proposed',
  trust_labels: [],
  policy_version: '1.0.0',
  ...over,
});

const eventButton = (type: string) => screen.getByRole('button', { name: new RegExp(`^${type.replace('.', '\\.')}`) });

describe('Trace event details', () => {
  it('expands an event and shows its recorded fields, stating what the backend did not record', async () => {
    const user = userEvent.setup();
    render(<TraceExplorer events={[ev('e1', { event_type: 'message.blocked', target_id: 'qa_agent', policy_decision: 'BLOCK', reason_code: 'THREAT_PROMPT_INJECTION' })]} />);
    const btn = eventButton('message.blocked');
    expect(btn).toHaveAttribute('aria-expanded', 'false');
    await user.click(btn);
    expect(btn).toHaveAttribute('aria-expanded', 'true');
    const detail = screen.getByRole('region', { name: 'Details for message.blocked' });
    expect(within(detail).getByText('e1')).toBeVisible();
    expect(within(detail).getByText('trace-1')).toBeVisible();
    expect(within(detail).getByText(/Parent link not recorded by the backend/)).toBeVisible();
    expect(within(detail).getByText(/Trust labels not recorded by the backend/)).toBeVisible();
    expect(within(detail).getByText(/No event in this run has a parent link/)).toBeVisible();
    await user.click(btn);
    expect(screen.queryByRole('region', { name: 'Details for message.blocked' })).not.toBeInTheDocument();
  });

  it('follows recorded parent and child links and moves focus to the target', async () => {
    const user = userEvent.setup();
    const events = [
      ev('p', { event_type: 'message.proposed' }),
      ev('d', { event_type: 'message.policy_decided', actor_id: 'communication_gateway', parent_event_id: 'p', policy_decision: 'ALLOW' }),
      ev('x', { event_type: 'message.delivered', parent_event_id: 'd', trust_labels: ['agent_generated'] }),
    ];
    render(<TraceExplorer events={events} />);
    await user.click(eventButton('message.delivered'));
    const detail = screen.getByRole('region', { name: 'Details for message.delivered' });
    expect(within(detail).getByText('agent_generated')).toBeVisible();
    expect(within(detail).getByRole('list', { name: 'Causal chain from root' })).toHaveTextContent('message.proposed→message.policy_decided→message.delivered');

    await user.click(within(detail).getByRole('button', { name: /message\.policy_decided \(communication_gateway\)/ }));
    expect(eventButton('message.policy_decided')).toHaveAttribute('aria-expanded', 'true');
    expect(eventButton('message.policy_decided')).toHaveFocus();
    const parentDetail = screen.getByRole('region', { name: 'Details for message.policy_decided' });
    expect(within(parentDetail).getByRole('button', { name: /message\.delivered/ })).toBeVisible(); // child link
  });

  it('reveals a linked event hidden by the current filters', async () => {
    const user = userEvent.setup();
    const events = [ev('p', { actor_id: 'orchestrator', event_type: 'workflow.started' }), ev('c', { parent_event_id: 'p' })];
    render(<TraceExplorer events={events} />);
    await user.selectOptions(screen.getByLabelText('Filter by agent'), 'backend_agent');
    await user.click(eventButton('message.proposed'));
    await user.click(screen.getByRole('button', { name: /workflow\.started \(orchestrator\)/ }));
    expect(eventButton('workflow.started')).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByLabelText('Filter by agent')).toHaveValue('');
  });

  it('shows metadata field names but never their values', async () => {
    const user = userEvent.setup();
    render(<TraceExplorer events={[ev('m', { payload_metadata: { api_key: 'sk-SECRET-123', rows: 5 } })]} />);
    await user.click(eventButton('message.proposed'));
    expect(screen.getByText('api_key, rows')).toBeVisible();
    expect(screen.queryByText(/sk-SECRET-123/)).not.toBeInTheDocument();
  });

  it('filters by threat type from THREAT_* reason codes', async () => {
    const user = userEvent.setup();
    render(
      <TraceExplorer
        events={[
          ev('1', { reason_code: 'THREAT_PROMPT_INJECTION', policy_decision: 'BLOCK' }),
          ev('2', { reason_code: 'THREAT_MEMORY_POISONING', policy_decision: 'QUARANTINE' }),
          ev('3', { reason_code: 'AUTHORIZED_PEER_COMMUNICATION', policy_decision: 'ALLOW' }),
        ]}
      />,
    );
    const select = screen.getByLabelText('Filter by threat type');
    expect(within(select).getAllByRole('option').map((o) => o.textContent)).toEqual(['All threat types', 'memory poisoning', 'prompt injection']);
    await user.selectOptions(select, 'THREAT_MEMORY_POISONING');
    expect(screen.getByRole('status')).toHaveTextContent('Showing 1 of 3 events');
  });

  it('disables the threat filter when the run had no threats', () => {
    render(<TraceExplorer events={[ev('1', { reason_code: 'AUTHORIZED_PEER_COMMUNICATION' })]} />);
    expect(screen.getByLabelText('Filter by threat type')).toBeDisabled();
  });
});
