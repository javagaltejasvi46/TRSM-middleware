import { apiRequest } from './client';
import { RunSummary, WorkflowConfig } from '../types';

export interface StartRunParams {
  workflow_id?: string;
  workflow?: WorkflowConfig;
  task: string;
  enable_trsm: boolean;
}

export const runsApi = {
  /** Synchronous on the backend: resolves only after the whole run has finished. */
  start: (params: StartRunParams) =>
    apiRequest<RunSummary>('/api/runs', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  get: (runId: string) => apiRequest<RunSummary>(`/api/runs/${runId}`),
};
