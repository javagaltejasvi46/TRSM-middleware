import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiRequest, describeErrorBody } from './client';

describe('describeErrorBody', () => {
  it('reads FastAPI string details', () => {
    expect(describeErrorBody('{"detail":"Run not found"}')).toBe('Run not found');
  });
  it('reads FastAPI validation error lists', () => {
    const body = JSON.stringify({ detail: [{ loc: ['body', 'workflow', 'nodes'], msg: 'List should have at least 1 item' }] });
    expect(describeErrorBody(body)).toBe('workflow.nodes: List should have at least 1 item');
  });
  it('reads structured details with a message and errors', () => {
    expect(describeErrorBody('{"detail":{"message":"Invalid workflow","errors":["Entry node missing"]}}')).toBe('Invalid workflow; Entry node missing');
  });
  it('falls back to the raw text for non-JSON bodies', () => {
    expect(describeErrorBody('Internal Server Error')).toBe('Internal Server Error');
    expect(describeErrorBody('')).toBe('empty response');
  });
});

describe('apiRequest', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('throws ApiError with the HTTP status and backend detail', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('{"detail":"Run not found"}', { status: 404 })));
    const err = (await apiRequest('/api/runs/x').catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(404);
    expect(err.message).toBe('/api/runs/x returned HTTP 404: Run not found');
  });

  it('reports an unreachable backend as status 0', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('Failed to fetch'); }));
    const err = (await apiRequest('/api/runs').catch((e: unknown) => e)) as ApiError;
    expect(err.status).toBe(0);
    expect(err.message).toMatch(/could not reach the backend/);
  });
});
