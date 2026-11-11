import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TraceExplorer } from './TraceExplorer';
import { AuditEvent } from '../../types';

const ev = (id: string, over: Partial<AuditEvent>): AuditEvent => ({
  event_id: id,
  run_id: 'r1',
  trace_id: 't1',
  timestamp: '2026-11-11T10:00:00.000Z',
  actor_id: 'backend_agent',
  event_type: 'message.proposed',
  trust_labels: [],
  ...over,
});

const events = [
  ev('1', { event_type: 'message.policy_decided', actor_id: 'communication_gateway', target_id: 'db_manager_agent', policy_decision: 'ALLOW', reason_code: 'AUTHORIZED_PEER_COMMUNICATION' }),
  ev('2', { event_type: 'message.blocked', target_id: 'qa_agent', policy_decision: 'BLOCK', reason_code: 'THREAT_PROMPT_INJECTION', trust_labels: ['untrusted_external'] }),
  ev('3', { event_type: 'workflow.started', actor_id: 'orchestrator' }),
];

const rows = () => within(screen.getByRole('list', { name: 'Trace events' })).getAllByRole('listitem');

describe('TraceExplorer', () => {
  it('shows an empty state and no filters before a run', () => {
    render(<TraceExplorer events={[]} />);
    expect(screen.getByText(/No trace events yet/)).toBeInTheDocument();
    expect(screen.queryByRole('search')).not.toBeInTheDocument();
  });

  it('renders decisions as text badges, reason codes and trust labels', () => {
    render(<TraceExplorer events={events} />);
    expect(rows()).toHaveLength(3);
    expect(within(screen.getByRole('list', { name: 'Trace events' })).getByText('BLOCK')).toBeVisible();
    expect(screen.getByText('THREAT_PROMPT_INJECTION')).toBeVisible();
    expect(screen.getByText('untrusted_external')).toBeVisible();
    expect(screen.getByRole('status')).toHaveTextContent('3 events recorded');
  });

  it('filters by decision and reports "Showing X of Y"', async () => {
    const user = userEvent.setup();
    render(<TraceExplorer events={events} />);
    await user.selectOptions(screen.getByLabelText('Filter by decision'), 'BLOCK');
    expect(rows()).toHaveLength(1);
    expect(screen.getByRole('status')).toHaveTextContent('Showing 1 of 3 events');
  });

  it('filters by agent and search, and shows a no-match state with a way out', async () => {
    const user = userEvent.setup();
    render(<TraceExplorer events={events} />);
    await user.selectOptions(screen.getByLabelText('Filter by agent'), 'qa_agent');
    expect(rows()).toHaveLength(1);
    await user.type(screen.getByLabelText('Search events'), 'nothing-matches-this');
    expect(screen.getByText(/No events match these filters/)).toBeInTheDocument();
    await user.click(screen.getAllByRole('button', { name: 'Clear filters' })[0]);
    expect(rows()).toHaveLength(3);
    expect(screen.getByLabelText('Search events')).toHaveValue('');
  });
});
