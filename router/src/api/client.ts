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
  RouteErrorResponse,
  RouterSettings,
  SettingsUpdateResponse,
  OllamaModel,
  ClientEntry,
  LogEntry,
  RouteHistoryEntry,
  IntegrationGuide,
  ServiceStatus,
  AgentDefinition,
  AgentCreateRequest,
  AgentRunRequest,
  AgentRunResponse,
  AgentSettings,
  AgentSettingsUpdate,
  AgentUpdateRequest,
  SkillDefinition,
  ActionDefinition,
  ActionProposalRequest,
  ActionProposalResponse,
  ActionExecuteRequest,
  ActionProposal,
  ActionResult,
  MemoryRunSummary,
  MemoryRunDetail,
  MemoryIncidentRead,
  MemoryIncidentCreate,
  MemoryIncidentFindingCreate,
  MemoryKnowledgeEntryRead,
  MemoryKnowledgeCreate,
  MemoryFeedbackEntryRead,
  MemoryFeedbackCreate,
} from '../types';
import { CONFIG } from '../config';

const BASE_URL = CONFIG.apiBaseUrl;
const DEFAULT_TIMEOUT = CONFIG.defaultTimeout;
const ROUTER_API_KEY_STORAGE_KEY = 'pi-guardian.routerApiKey';
const ADMIN_SESSION_PATH = '/auth/bootstrap';

let adminBootstrapPromise: Promise<void> | null = null;
let adminBootstrapReady = false;

export function getStoredRouterApiKey(): string {
  if (typeof window === 'undefined') return '';
  return window.localStorage.getItem(ROUTER_API_KEY_STORAGE_KEY) || '';
}

export function setStoredRouterApiKey(apiKey: string): void {
  if (typeof window === 'undefined') return;
  const normalized = apiKey.trim();
  if (normalized) {
    window.localStorage.setItem(ROUTER_API_KEY_STORAGE_KEY, normalized);
  } else {
    window.localStorage.removeItem(ROUTER_API_KEY_STORAGE_KEY);
  }
}

function normalizePath(path: string): string {
  return path.split('?')[0] || path;
}

function requiresAdminSession(path: string): boolean {
  const normalized = normalizePath(path);
  return (
    normalized === '/integration' ||
    normalized === '/settings' ||
    normalized === '/models' ||
    normalized === '/models/select' ||
    normalized === '/status/service' ||
    normalized === '/clients' ||
    normalized === '/history' ||
    normalized === '/logs' ||
    normalized === '/agents' ||
    normalized === '/skills' ||
    normalized === '/actions' ||
    normalized === '/route' ||
    normalized === '/memory'
  );
}

async function ensureAdminSession(): Promise<void> {
  if (typeof window === 'undefined') return;
  if (getStoredRouterApiKey()) return;
  if (adminBootstrapReady) return;
  if (!adminBootstrapPromise) {
    adminBootstrapPromise = fetch(`${BASE_URL}${ADMIN_SESSION_PATH}`, {
      method: 'POST',
      credentials: 'include',
    }).then((response) => {
      if (!response.ok && response.status !== 204) {
        throw new Error(`Admin bootstrap fehlgeschlagen: ${response.status}`);
      }
      adminBootstrapReady = true;
    }).finally(() => {
      adminBootstrapPromise = null;
    });
  }
  await adminBootstrapPromise;
}

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
  const apiKey = getStoredRouterApiKey();

  try {
    if (requiresAdminSession(path)) {
      await ensureAdminSession().catch(() => {});
    }
    const response = await fetch(`${BASE_URL}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey ? { 'X-API-Key': apiKey } : {}),
        ...fetchOptions.headers,
      },
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      let parsedError: RouteErrorResponse | null = null;
      try {
        parsedError = JSON.parse(body) as RouteErrorResponse;
      } catch {
        parsedError = null;
      }
      throw new ApiRequestError(
        parsedError?.error?.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        body,
        parsedError?.error?.code,
        parsedError?.request_id,
        parsedError?.error?.retryable ?? false
      );
    }

    if (response.status === 204) {
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
  code?: string;
  requestId?: string;
  retryable: boolean;

  constructor(
    message: string,
    status: number,
    body: string,
    code?: string,
    requestId?: string,
    retryable = false
  ) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.body = body;
    this.timestamp = new Date().toISOString();
    this.code = code;
    this.requestId = requestId;
    this.retryable = retryable;
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
export async function updateSettings(
  settings: Partial<RouterSettings> & { restart_service?: boolean }
): Promise<SettingsUpdateResponse> {
  return apiFetch<SettingsUpdateResponse>('/settings', {
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
export async function updateClient(id: number, client: Partial<ClientEntry>): Promise<ClientEntry> {
  return apiFetch<ClientEntry>(`/clients/${id}`, {
    method: 'PUT',
    body: JSON.stringify(client),
  });
}

/** DELETE /clients/:id – Client entfernen */
export async function deleteClient(id: number): Promise<void> {
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

/** GET /integration – Sichere Integrationshilfe für neue Clients */
export async function fetchIntegrationGuide(): Promise<IntegrationGuide> {
  return apiFetch<IntegrationGuide>('/integration');
}

/** GET /history – Letzte Router-Anfragen */
export async function fetchRouteHistory(limit = 50): Promise<RouteHistoryEntry[]> {
  return apiFetch<RouteHistoryEntry[]>(`/history?limit=${limit}`);
}

/** GET /agents – Registrierte Agenten abrufen */
export async function fetchAgents(): Promise<AgentDefinition[]> {
  return apiFetch<AgentDefinition[]>('/agents');
}

export async function fetchSkills(): Promise<SkillDefinition[]> {
  return apiFetch<SkillDefinition[]>('/skills');
}

export async function fetchActions(): Promise<ActionDefinition[]> {
  return apiFetch<ActionDefinition[]>('/actions');
}

export async function fetchMemoryRuns(): Promise<MemoryRunSummary[]> {
  return apiFetch<MemoryRunSummary[]>('/memory/runs');
}

export async function fetchMemoryRun(runId: string): Promise<MemoryRunDetail> {
  return apiFetch<MemoryRunDetail>(`/memory/runs/${encodeURIComponent(runId)}`);
}

export async function fetchMemoryIncidents(): Promise<MemoryIncidentRead[]> {
  return apiFetch<MemoryIncidentRead[]>('/memory/incidents');
}

export async function fetchMemoryIncident(incidentId: number): Promise<MemoryIncidentRead> {
  return apiFetch<MemoryIncidentRead>(`/memory/incidents/${incidentId}`);
}

export async function fetchMemoryKnowledge(): Promise<MemoryKnowledgeEntryRead[]> {
  return apiFetch<MemoryKnowledgeEntryRead[]>('/memory/knowledge');
}

export async function fetchMemoryFeedback(): Promise<MemoryFeedbackEntryRead[]> {
  return apiFetch<MemoryFeedbackEntryRead[]>('/memory/feedback');
}

export async function createMemoryIncident(payload: MemoryIncidentCreate): Promise<MemoryIncidentRead> {
  return apiFetch<MemoryIncidentRead>('/memory/incidents', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function addMemoryIncidentFinding(
  incidentId: number,
  payload: MemoryIncidentFindingCreate
): Promise<MemoryIncidentRead> {
  return apiFetch<MemoryIncidentRead>(`/memory/incidents/${incidentId}/findings`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function createMemoryKnowledge(payload: MemoryKnowledgeCreate): Promise<MemoryKnowledgeEntryRead> {
  return apiFetch<MemoryKnowledgeEntryRead>('/memory/knowledge', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function createMemoryFeedback(payload: MemoryFeedbackCreate): Promise<MemoryFeedbackEntryRead> {
  return apiFetch<MemoryFeedbackEntryRead>('/memory/feedback', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/** GET /agents/:name – Einzelnen Agenten abrufen */
export async function fetchAgent(agentName: string): Promise<AgentDefinition> {
  return apiFetch<AgentDefinition>(`/agents/${encodeURIComponent(agentName)}`);
}

/** GET /agents/:name/settings – Agenten-Settings abrufen */
export async function fetchAgentSettings(agentName: string): Promise<AgentSettings> {
  return apiFetch<AgentSettings>(`/agents/${encodeURIComponent(agentName)}/settings`);
}

/** POST /agents – Agent anlegen */
export async function createAgent(payload: AgentCreateRequest): Promise<AgentDefinition> {
  return apiFetch<AgentDefinition>('/agents', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/** PUT /agents/:name – Agent aktualisieren */
export async function updateAgent(
  agentName: string,
  payload: AgentUpdateRequest
): Promise<AgentDefinition> {
  return apiFetch<AgentDefinition>(`/agents/${encodeURIComponent(agentName)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

/** PUT /agents/:name/settings – Agenten-Settings aktualisieren */
export async function updateAgentSettings(
  agentName: string,
  payload: AgentSettingsUpdate
): Promise<AgentDefinition> {
  return apiFetch<AgentDefinition>(`/agents/${encodeURIComponent(agentName)}/settings`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

/** POST /agents/:name/enable – Agent aktivieren */
export async function enableAgent(agentName: string): Promise<AgentDefinition> {
  return apiFetch<AgentDefinition>(`/agents/${encodeURIComponent(agentName)}/enable`, {
    method: 'POST',
  });
}

/** POST /agents/:name/disable – Agent deaktivieren */
export async function disableAgent(agentName: string): Promise<AgentDefinition> {
  return apiFetch<AgentDefinition>(`/agents/${encodeURIComponent(agentName)}/disable`, {
    method: 'POST',
  });
}

/** DELETE /agents/:name – Custom-Agent löschen */
export async function deleteAgent(agentName: string): Promise<void> {
  await apiFetch<void>(`/agents/${encodeURIComponent(agentName)}`, {
    method: 'DELETE',
  });
}

/** POST /agents/run – Agenten-Testlauf ausführen */
export async function runAgent(payload: AgentRunRequest): Promise<AgentRunResponse> {
  return apiFetch<AgentRunResponse>('/agents/run', {
    method: 'POST',
    body: JSON.stringify(payload),
    timeout: CONFIG.modelTimeout,
  });
}

export async function proposeAction(
  payload: ActionProposalRequest
): Promise<ActionProposalResponse> {
  return apiFetch<ActionProposalResponse>('/actions/propose', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function executeAction(
  payload: ActionExecuteRequest
): Promise<ActionResult> {
  return apiFetch<ActionResult>('/actions/execute', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
