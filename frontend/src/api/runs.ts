import { apiRequest } from './client';
import { WorkflowConfig } from '../types';

export interface StartRunParams {
  workflow_id?: string;
  workflow?: WorkflowConfig;
  task: string;
  enable_trsm: boolean;
}

export const runsApi = {
  start: (params: StartRunParams) =>
    apiRequest<any>('/api/runs', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  get: (runId: string) => apiRequest<any>(`/api/runs/${runId}`),
};
