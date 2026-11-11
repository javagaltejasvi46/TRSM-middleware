import { apiRequest } from './client';
import { WorkflowConfig, WorkflowValidationResult } from '../types';

export const workflowsApi = {
  validate: (workflow: WorkflowConfig) =>
    apiRequest<WorkflowValidationResult>(
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
