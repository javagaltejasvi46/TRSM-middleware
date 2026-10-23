import { apiRequest } from './client';
import { AuditEvent } from '../types';

export const eventsApi = {
  getEvents: (runId: string, eventType?: string, actorId?: string) => {
    const params = new URLSearchParams();
    if (eventType) params.append('event_type', eventType);
    if (actorId) params.append('actor_id', actorId);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiRequest<AuditEvent[]>(`/api/runs/${runId}/events${qs}`);
  },
  getTraceGraph: (runId: string) =>
    apiRequest<any>(`/api/runs/${runId}/trace`),
};
