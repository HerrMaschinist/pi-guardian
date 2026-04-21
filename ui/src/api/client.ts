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

function isAbsoluteUrl(value: string): boolean {
  return /^https?:\/\//i.test(value);
}

function normalizeBasePath(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return '/';
  }
  if (isAbsoluteUrl(trimmed)) {
    return trimmed.replace(/\/+$/, '');
  }
  const withLeadingSlash = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
  return withLeadingSlash.replace(/\/+$/, '') || '/';
}

function normalizeEndpoint(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return '/';
  }
  return trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
}

export function buildGuardianApiUrl(basePath: string, endpoint: string): string {
  const normalizedBasePath = normalizeBasePath(basePath);
  const normalizedEndpoint = normalizeEndpoint(endpoint);

  if (isAbsoluteUrl(normalizedBasePath)) {
    const suffix = normalizedEndpoint.replace(/^\//, '');
    return new URL(suffix, `${normalizedBasePath}/`).toString();
  }

  if (normalizedBasePath === '/') {
    return normalizedEndpoint;
  }

  return `${normalizedBasePath}${normalizedEndpoint}`;
}

async function fetchJson<T>(url: string, options: FetchOptions = {}): Promise<T> {
  const { timeout = 10_000, ...requestOptions } = options;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeout);

  try {
    const headers = new Headers(requestOptions.headers ?? {});
    headers.set('Accept', 'application/json');

    const response = await fetch(url, {
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

export function describeGuardianApiError(error: unknown, fallback: string): string {
  if (error instanceof ApiRequestError) {
    if (error.status > 0) {
      return `HTTP ${error.status}: ${error.body || error.message}`;
    }
    return error.message || fallback;
  }
  if (error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}

export async function fetchGuardianStatus(basePath = CONFIG.apiBasePath): Promise<GuardianStatusResponse> {
  return fetchJson<GuardianStatusResponse>(buildGuardianApiUrl(basePath, '/health'), { timeout: 15_000 });
}

export async function fetchGuardianHistory(
  limit = CONFIG.historyLimit,
  basePath = CONFIG.apiBasePath,
): Promise<GuardianHistoryResponse> {
  const safeLimit = Number.isFinite(limit) ? Math.max(Math.trunc(limit), 1) : CONFIG.historyLimit;
  return fetchJson<GuardianHistoryResponse>(
    buildGuardianApiUrl(basePath, `/history?limit=${safeLimit}`),
    { timeout: 15_000 },
  );
}

export async function fetchGuardianDashboard(basePath = CONFIG.apiBasePath): Promise<GuardianDashboardPayload> {
  const [status, history] = await Promise.all([
    fetchGuardianStatus(basePath),
    fetchGuardianHistory(CONFIG.historyLimit, basePath),
  ]);
  return { status, history };
}
