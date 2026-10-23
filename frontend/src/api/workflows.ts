import { apiRequest } from './client';
import { WorkflowConfig } from '../types';

export const workflowsApi = {
  validate: (workflow: WorkflowConfig) =>
    apiRequest<{ is_valid: boolean; errors: string[]; warnings: string[] }>(
      '/api/workflows/validate',
      { method: 'POST', body: JSON.stringify(workflow) }
    ),
  create: (workflow: WorkflowConfig) =>
    apiRequest<WorkflowConfig>('/api/workflows', {
      method: 'POST',
      body: JSON.stringify(workflow),
    }),
  list: () => apiRequest<WorkflowConfig[]>('/api/workflows'),
  get: (workflowId: string) =>
    apiRequest<WorkflowConfig>(`/api/workflows/${workflowId}`),
};
