// === Bestehende API-Typen (SOFORT NUTZBAR) ===

export interface HealthResponse {
  status: string;
}

export interface RouteRequest {
  prompt: string;
  preferred_model?: string;
  stream?: boolean;
}

export interface RouteResponse {
  model: string;
  response: string;
  done: boolean;
  done_reason: string;
}

// === Geplante API-Typen (BACKEND ERFORDERLICH) ===

export interface RouterSettings {
  router_host: string;
  router_port: number;
  ollama_host: string;
  ollama_port: number;
  timeout: number;
  default_model: string;
  logging_level: string;
  stream_default: boolean;
}

export interface OllamaModel {
  name: string;
  size: string;
  modified_at: string;
  digest: string;
}

export interface ClientEntry {
  id: string;
  name: string;
  description: string;
  active: boolean;
  allowed_ip: string;
  allowed_routes: string[];
  api_key?: string;
}

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error';
  source: string;
  message: string;
}

export interface ServiceStatus {
  service: string;
  active: boolean;
  uptime: string;
  pid: number;
  memory_usage: string;
  cpu_percent: number;
}

// === UI-interne Typen ===

export type Page = 'dashboard' | 'models' | 'clients' | 'settings' | 'diagnostics' | 'logs';

export interface ApiError {
  message: string;
  status?: number;
  timestamp: string;
}

export type ConnectionState = 'connected' | 'disconnected' | 'checking' | 'error';
