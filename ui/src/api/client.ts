/**
 * PI Guardian API Client
 *
 * Zentrale Stelle für Backend-Kommunikation.
 * Verwendet den Vite-Proxy (/api -> http://127.0.0.1:8071).
 *
 * Im Production-Build muss die BASE_URL auf den tatsächlichen Host gesetzt werden,
 * da kein Vite-Dev-Server mehr als Proxy dient.
 */

import type {
  HealthResponse,
  RouteRequest,
  RouteResponse,
  RouterSettings,
  SettingsUpdateResponse,
  OllamaModel,
  ClientEntry,
  LogEntry,
  ServiceStatus,
  AgentDefinition,
  SkillDefinition,
  ActionDefinition,
  RouteHistoryEntry,
  MemoryRunSummary,
  MemoryRunDetail,
  MemoryIncidentRead,
  MemoryKnowledgeEntryRead,
  MemoryFeedbackEntryRead,
  ModelRegistryEntry,
  ModelPullJob,
} from '../types';
import { CONFIG } from '../config';

const BASE_URL = CONFIG.apiBaseUrl;
const DEFAULT_TIMEOUT = CONFIG.defaultTimeout;
const ROUTER_API_KEY_STORAGE_KEY = 'pi-guardian.routerApiKey';
type RouterAuthMode = 'unknown' | 'cookie' | 'key';

let routerAuthMode: RouterAuthMode = 'unknown';
let bootstrapSessionPromise: Promise<boolean> | null = null;

// =========================================================
// Basis-Fetch mit Timeout und Fehlerbehandlung
// =========================================================

interface FetchOptions extends RequestInit {
  timeout?: number;
}

export function getStoredRouterApiKey(): string {
  if (typeof window === 'undefined') return '';
  try {
    return window.localStorage.getItem(ROUTER_API_KEY_STORAGE_KEY) ?? '';
  } catch {
    return '';
  }
}

export function setStoredRouterApiKey(apiKey: string): void {
  if (typeof window === 'undefined') return;
  try {
    if (apiKey.trim()) {
      window.localStorage.setItem(ROUTER_API_KEY_STORAGE_KEY, apiKey.trim());
      routerAuthMode = 'key';
    } else {
      window.localStorage.removeItem(ROUTER_API_KEY_STORAGE_KEY);
      routerAuthMode = 'unknown';
    }
  } catch {
    // Ignore storage failures and fall back to in-memory usage.
  }
}

export function clearStoredRouterApiKey(): void {
  setStoredRouterApiKey('');
}

function buildHeaders(fetchHeaders: HeadersInit | undefined): Headers {
  const headers = new Headers(fetchHeaders ?? {});
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (routerAuthMode === 'cookie') {
    return headers;
  }
  const apiKey = getStoredRouterApiKey();
  if (apiKey) {
    headers.set('X-API-Key', apiKey);
  }
  return headers;
}

async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  return apiFetchWithAuthRetry<T>(path, options, true);
}

async function apiFetchWithAuthRetry<T>(
  path: string,
  options: FetchOptions = {},
  allowAuthRetry: boolean,
): Promise<T> {
  const { timeout = DEFAULT_TIMEOUT, ...fetchOptions } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
      credentials: 'include',
      headers: buildHeaders(fetchOptions.headers),
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      if (allowAuthRetry && (response.status === 401 || response.status === 403) && path !== '/auth/bootstrap') {
        const bootstrapped = await ensureRouterAdminSession();
        if (bootstrapped) {
          return apiFetchWithAuthRetry<T>(path, options, false);
        }
      }
      throw new ApiRequestError(
        `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        body
      );
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const contentLength = response.headers.get('content-length');
    if (contentLength === '0') {
      return undefined as T;
    }

    return await response.json();
  } catch (err) {
    if (err instanceof ApiRequestError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiRequestError(`Timeout nach ${timeout}ms`, 0, '');
    }
    throw new ApiRequestError(
      err instanceof Error ? err.message : 'Unbekannter Fehler',
      0,
      ''
    );
  } finally {
    clearTimeout(timer);
  }
}

export class ApiRequestError extends Error {
  status: number;
  body: string;
  timestamp: string;

  constructor(message: string, status: number, body: string) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.body = body;
    this.timestamp = new Date().toISOString();
  }
}

/**
 * Versucht, die persistente Router-Admin-Session per Bootstrap-Cookie zu erneuern.
 * Wenn das klappt, werden nachfolgende Requests ohne X-API-Key gesendet.
 */
export async function ensureRouterAdminSession(): Promise<boolean> {
  if (bootstrapSessionPromise) {
    return bootstrapSessionPromise;
  }

  bootstrapSessionPromise = (async () => {
    try {
      const response = await fetch(`${BASE_URL}/auth/bootstrap`, {
        method: 'POST',
        credentials: 'include',
      });
      if (response.ok) {
        routerAuthMode = 'cookie';
        return true;
      }
    } catch {
      // Fällt auf den lokalen API-Key zurück.
    }

    routerAuthMode = getStoredRouterApiKey() ? 'key' : 'unknown';
    return false;
  })();

  return bootstrapSessionPromise;
}

// =========================================================
// SOFORT NUTZBAR – Bestehende Endpunkte
// =========================================================

/** GET /health – Prüft ob der Router erreichbar ist */
export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health');
}

/** POST /route – Sendet einen Prompt an den Router */
export async function sendRoute(request: RouteRequest): Promise<RouteResponse> {
  return apiFetch<RouteResponse>('/route', {
    method: 'POST',
    body: JSON.stringify(request),
    timeout: CONFIG.modelTimeout,
  });
}

// =========================================================
// BACKEND ERFORDERLICH – Geplante Endpunkte
// =========================================================

/** GET /settings – Router-Konfiguration abrufen */
export async function fetchSettings(): Promise<RouterSettings> {
  return apiFetch<RouterSettings>('/settings');
}

/** PUT /settings – Router-Konfiguration ändern */
export async function updateSettings(settings: Partial<RouterSettings>): Promise<SettingsUpdateResponse> {
  return apiFetch<SettingsUpdateResponse>('/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}

/** GET /models – Verfügbare Ollama-Modelle abrufen */
export async function fetchModels(): Promise<OllamaModel[]> {
  return apiFetch<OllamaModel[]>('/models');
}

/** GET /models/registry – Persistente Modellregistrierung abrufen */
export async function fetchModelRegistry(): Promise<ModelRegistryEntry[]> {
  return apiFetch<ModelRegistryEntry[]>('/models/registry');
}

/** POST /models/registry – Neues Modell registrieren */
export async function createModelRegistryEntry(
  entry: Omit<ModelRegistryEntry, 'id' | 'role' | 'created_at' | 'updated_at'> & { description?: string },
): Promise<ModelRegistryEntry> {
  return apiFetch<ModelRegistryEntry>('/models/registry', {
    method: 'POST',
    body: JSON.stringify(entry),
  });
}

/** PUT /models/registry/:id – Registriertes Modell aktualisieren */
export async function updateModelRegistryEntry(
  id: number,
  entry: Partial<Pick<ModelRegistryEntry, 'name' | 'description' | 'enabled'>>,
): Promise<ModelRegistryEntry> {
  return apiFetch<ModelRegistryEntry>(`/models/registry/${id}`, {
    method: 'PUT',
    body: JSON.stringify(entry),
  });
}

/** DELETE /models/registry/:id – Registriertes Modell löschen */
export async function deleteModelRegistryEntry(id: number): Promise<void> {
  await apiFetch<void>(`/models/registry/${id}`, {
    method: 'DELETE',
  });
}

/** GET /models/pull – Modell-Download-Jobs abrufen */
export async function fetchModelPullJobs(limit = 10): Promise<ModelPullJob[]> {
  return apiFetch<ModelPullJob[]>(`/models/pull?limit=${encodeURIComponent(String(limit))}`);
}

/** POST /models/pull – Modell-Download starten */
export async function createModelPullJob(modelName: string): Promise<ModelPullJob> {
  return apiFetch<ModelPullJob>('/models/pull', {
    method: 'POST',
    body: JSON.stringify({ model_name: modelName }),
  });
}

/** GET /models/pull/:id – Job-Status abrufen */
export async function fetchModelPullJob(jobId: number): Promise<ModelPullJob> {
  return apiFetch<ModelPullJob>(`/models/pull/${jobId}`);
}

/** POST /models/select – Standardmodell setzen */
export async function selectModel(modelName: string): Promise<{ model: string }> {
  return apiFetch<{ model: string }>('/models/select', {
    method: 'POST',
    body: JSON.stringify({ model: modelName }),
  });
}

/** GET /clients – Registrierte Clients abrufen */
export async function fetchClients(): Promise<ClientEntry[]> {
  return apiFetch<ClientEntry[]>('/clients');
}

/** POST /clients – Neuen Client registrieren */
export async function createClient(client: Omit<ClientEntry, 'id'>): Promise<ClientEntry> {
  return apiFetch<ClientEntry>('/clients', {
    method: 'POST',
    body: JSON.stringify(client),
  });
}

/** PUT /clients/:id – Client aktualisieren */
export async function updateClient(id: string, client: Partial<ClientEntry>): Promise<ClientEntry> {
  return apiFetch<ClientEntry>(`/clients/${id}`, {
    method: 'PUT',
    body: JSON.stringify(client),
  });
}

/** DELETE /clients/:id – Client entfernen */
export async function deleteClient(id: string): Promise<void> {
  await apiFetch<void>(`/clients/${id}`, { method: 'DELETE' });
}

/** GET /logs – Letzte Log-Einträge */
export async function fetchLogs(limit = 50): Promise<LogEntry[]> {
  return apiFetch<LogEntry[]>(`/logs?limit=${limit}`);
}

/** GET /status/service – Systemstatus des Router-Dienstes */
export async function fetchServiceStatus(): Promise<ServiceStatus> {
  return apiFetch<ServiceStatus>('/status/service');
}

export async function fetchAgents(): Promise<AgentDefinition[]> {
  return apiFetch<AgentDefinition[]>('/agents');
}

export async function fetchSkills(): Promise<SkillDefinition[]> {
  return apiFetch<SkillDefinition[]>('/skills');
}

export async function fetchActions(): Promise<ActionDefinition[]> {
  return apiFetch<ActionDefinition[]>('/actions');
}

export async function fetchRouteHistory(limit = 50): Promise<RouteHistoryEntry[]> {
  return apiFetch<RouteHistoryEntry[]>(`/history?limit=${limit}`);
}

export async function fetchMemoryRuns(): Promise<MemoryRunSummary[]> {
  return apiFetch<MemoryRunSummary[]>('/memory');
}

export async function fetchMemoryRunDetail(runId: string): Promise<MemoryRunDetail> {
  return apiFetch<MemoryRunDetail>(`/memory/runs/${runId}`);
}

export async function fetchMemoryIncidents(): Promise<MemoryIncidentRead[]> {
  return apiFetch<MemoryIncidentRead[]>('/memory/incidents');
}

export async function fetchMemoryKnowledge(): Promise<MemoryKnowledgeEntryRead[]> {
  return apiFetch<MemoryKnowledgeEntryRead[]>('/memory/knowledge');
}

export async function fetchMemoryFeedback(): Promise<MemoryFeedbackEntryRead[]> {
  return apiFetch<MemoryFeedbackEntryRead[]>('/memory/feedback');
}
