/**
 * PI Guardian API Client
 *
 * Zentrale Stelle für Backend-Kommunikation.
 * Verwendet den Vite-Proxy (/api -> http://192.168.50.10:8071).
 *
 * Im Production-Build muss die BASE_URL auf den tatsächlichen Host gesetzt werden,
 * da kein Vite-Dev-Server mehr als Proxy dient.
 */

import type {
  HealthResponse,
  RouteRequest,
  RouteResponse,
  RouterSettings,
  OllamaModel,
  ClientEntry,
  LogEntry,
  ServiceStatus,
} from '../types';
import { CONFIG } from '../config';

const BASE_URL = CONFIG.apiBaseUrl;
const DEFAULT_TIMEOUT = CONFIG.defaultTimeout;

// =========================================================
// Basis-Fetch mit Timeout und Fehlerbehandlung
// =========================================================

interface FetchOptions extends RequestInit {
  timeout?: number;
}

async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { timeout = DEFAULT_TIMEOUT, ...fetchOptions } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers,
      },
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new ApiRequestError(
        `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        body
      );
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
export async function updateSettings(settings: Partial<RouterSettings>): Promise<RouterSettings> {
  return apiFetch<RouterSettings>('/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}

/** GET /models – Verfügbare Ollama-Modelle abrufen */
export async function fetchModels(): Promise<OllamaModel[]> {
  return apiFetch<OllamaModel[]>('/models');
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
