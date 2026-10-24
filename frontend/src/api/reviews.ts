import { apiRequest } from './client';

export interface ReviewRecord {
  review_id: string;
  run_id: string;
  trace_id: string;
  event_id: string;
  actor_id: string;
  action_type: string;
  target: string;
  status: 'pending' | 'resolved';
  decision?: string | null;
  reviewer_comment?: string | null;
}

export const reviewsApi = {
  list: () => apiRequest<ReviewRecord[]>('/api/reviews'),
  get: (reviewId: string) => apiRequest<ReviewRecord>(`/api/reviews/${reviewId}`),
  resolve: (reviewId: string, decision: 'ALLOW' | 'BLOCK', comment: string) =>
    apiRequest<ReviewRecord>(`/api/reviews/${reviewId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ decision, reviewer_comment: comment }),
    }),
};
