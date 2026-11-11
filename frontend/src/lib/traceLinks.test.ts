import { describe, expect, it } from 'vitest';
import { ancestry, buildEventIndex, parentOf } from './traceLinks';
import { AuditEvent } from '../types';

const ev = (id: string, parent: string | null = null): AuditEvent => ({
  event_id: id,
  parent_event_id: parent,
  run_id: 'r',
  trace_id: 't',
  timestamp: '2026-11-11T10:00:00Z',
  actor_id: 'a',
  event_type: 'message.proposed',
  trust_labels: [],
});

describe('traceLinks', () => {
  it('reports no links when the backend recorded none (current backend behaviour)', () => {
    const idx = buildEventIndex([ev('1'), ev('2')]);
    expect(idx.hasAnyLinks).toBe(false);
    expect(parentOf(ev('2'), idx)).toEqual({ kind: 'none' });
    expect(ancestry(ev('2'), idx).map((e) => e.event_id)).toEqual(['2']);
  });

  it('indexes recorded parents and children without inferring any', () => {
    const events = [ev('root'), ev('mid', 'root'), ev('leaf', 'mid'), ev('sibling', 'root')];
    const idx = buildEventIndex(events);
    expect(idx.hasAnyLinks).toBe(true);
    expect(idx.children.get('root')!.map((e) => e.event_id)).toEqual(['mid', 'sibling']);
    expect(parentOf(events[2], idx)).toMatchObject({ kind: 'in-run', parent: { event_id: 'mid' } });
    expect(ancestry(events[2], idx).map((e) => e.event_id)).toEqual(['root', 'mid', 'leaf']);
  });

  it('flags a recorded parent that is not among the run events', () => {
    const idx = buildEventIndex([ev('x', 'elsewhere')]);
    expect(parentOf(ev('x', 'elsewhere'), idx)).toEqual({ kind: 'missing', parentId: 'elsewhere' });
  });

  it('stops on a cycle instead of looping forever', () => {
    const events = [ev('a', 'b'), ev('b', 'a')];
    const idx = buildEventIndex(events);
    expect(ancestry(events[0], idx).map((e) => e.event_id)).toEqual(['b', 'a']);
  });
});
