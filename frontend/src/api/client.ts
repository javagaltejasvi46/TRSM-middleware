/**
 * HTTP Client for TRSM Backend API.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/** A failed request: HTTP status (0 = no response) plus the backend's own detail when it sent one. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly endpoint: string,
    public readonly detail: string,
  ) {
    super(status ? `${endpoint} returned HTTP ${status}: ${detail}` : `${endpoint}: ${detail}`);
    this.name = 'ApiError';
  }
}

/** Turn a FastAPI error body ({"detail": "..."} / {"detail": [...]} / {"detail": {...}}) into readable text. */
export function describeErrorBody(body: string): string {
  try {
    const parsed = JSON.parse(body);
    const d = parsed?.detail ?? parsed;
    if (typeof d === 'string') return d;
    if (Array.isArray(d)) {
      return d.map((x) => (x?.loc && x?.msg ? `${x.loc.filter((p: unknown) => p !== 'body').join('.')}: ${x.msg}` : JSON.stringify(x))).join('; ');
    }
    if (d && typeof d === 'object') {
      const parts = [d.message, ...(Array.isArray(d.errors) ? d.errors : [])].filter(Boolean);
      return parts.length ? parts.join('; ') : JSON.stringify(d);
    }
    return String(d);
  } catch {
    return body.trim() || 'empty response';
  }
}

export async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  let response: Response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (e) {
    throw new ApiError(0, endpoint, `could not reach the backend at ${BASE_URL} (${(e as Error).message})`);
  }
  if (!response.ok) {
    throw new ApiError(response.status, endpoint, describeErrorBody(await response.text()));
  }
  return response.json();
}
