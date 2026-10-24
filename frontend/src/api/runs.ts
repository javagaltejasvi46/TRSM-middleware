import { apiRequest } from './client';
import { WorkflowConfig } from '../types';

export interface StartRunParams {
  workflow_id?: string;
  workflow?: WorkflowConfig;
  task: string;
  enable_trsm: boolean;
  use_ollama?: boolean;
}

export interface RunSummary {
  run_id: string;
  workflow_id: string;
  status: string;
  enable_trsm: boolean;
  task: string;
  total_messages: number;
  total_tool_calls: number;
  blocked_actions: number;
}

export interface RunStatus {
  run_id: string;
  workflow_id: string;
  status: string;
  enable_trsm: boolean;
}

export const runsApi = {
  start: (params: StartRunParams) =>
    apiRequest<RunSummary>('/api/runs', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  get: (runId: string) => apiRequest<RunSummary>(`/api/runs/${runId}`),
  getStatus: (runId: string) => apiRequest<RunStatus>(`/api/runs/${runId}/status`),
  list: () => apiRequest<RunSummary[]>('/api/runs'),
};
