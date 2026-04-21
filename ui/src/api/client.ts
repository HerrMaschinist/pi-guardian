import { CONFIG } from '../config';
import type {
  GuardianDashboardPayload,
  GuardianHistoryResponse,
  GuardianStatusResponse,
} from '../types';

export class ApiRequestError extends Error {
  status: number;
  body: string;

  constructor(message: string, status: number, body: string) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.body = body;
  }
}

interface FetchOptions extends RequestInit {
  timeout?: number;
}

async function fetchJson<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { timeout = 10_000, ...requestOptions } = options;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeout);

  try {
    const headers = new Headers(requestOptions.headers ?? {});
    headers.set('Accept', 'application/json');

    const response = await fetch(`${CONFIG.apiBaseUrl}${path}`, {
      ...requestOptions,
      credentials: 'include',
      signal: controller.signal,
      headers,
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new ApiRequestError(`HTTP ${response.status}: ${response.statusText}`, response.status, body);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const contentLength = response.headers.get('content-length');
    if (contentLength === '0') {
      return undefined as T;
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiRequestError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiRequestError(`Timeout nach ${timeout}ms`, 0, '');
    }
    throw new ApiRequestError(error instanceof Error ? error.message : 'Unbekannter Fehler', 0, '');
  } finally {
    window.clearTimeout(timer);
  }
}

export async function fetchGuardianStatus(baseUrl = CONFIG.apiBaseUrl): Promise<GuardianStatusResponse> {
  return fetchJson<GuardianStatusResponse>(`${baseUrl}/health`, { timeout: 15_000 });
}

export async function fetchGuardianHistory(
  limit = CONFIG.historyLimit,
  baseUrl = CONFIG.apiBaseUrl,
): Promise<GuardianHistoryResponse> {
  const safeLimit = Number.isFinite(limit) ? Math.max(Math.trunc(limit), 1) : CONFIG.historyLimit;
  return fetchJson<GuardianHistoryResponse>(`${baseUrl}/history?limit=${safeLimit}`, { timeout: 15_000 });
}

export async function fetchGuardianDashboard(baseUrl = CONFIG.apiBaseUrl): Promise<GuardianDashboardPayload> {
  const [status, history] = await Promise.all([fetchGuardianStatus(baseUrl), fetchGuardianHistory(CONFIG.historyLimit, baseUrl)]);
  return { status, history };
}
