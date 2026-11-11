import { apiRequest } from './client';
import { RunComparison, RunMetrics } from '../types';

export const metricsApi = {
  getRunMetrics: (runId: string) =>
    apiRequest<RunMetrics>(`/api/runs/${runId}/metrics`),
  compareRuns: (baselineRun: string, protectedRun: string) =>
    apiRequest<RunComparison>(
      `/api/evaluations/compare?baseline_run=${encodeURIComponent(
        baselineRun
      )}&protected_run=${encodeURIComponent(protectedRun)}`
    ),
};
