/**
 * Zentrale Konfiguration.
 *
 * Alle Infrastrukturwerte an einer Stelle.
 * Kann später durch GET /settings vom Backend ersetzt werden.
 *
 * Umgebungsvariablen (optional, via .env oder Build):
 *   VITE_ROUTER_HOST    – z.B. 127.0.0.1
 *   VITE_ROUTER_PORT    – z.B. 8071
 *   VITE_DEFAULT_MODEL  – z.B. qwen2.5-coder:1.5b
 *   VITE_LARGE_MODEL    – z.B. qwen2.5-coder:3b
 *   VITE_API_URL        – z.B. http://192.168.50.10:8071 (für Production ohne Proxy)
 */

export const CONFIG = {
  /** Router-Host im LAN */
  routerHost: import.meta.env.VITE_ROUTER_HOST || '127.0.0.1',

  /** Router-Port */
  routerPort: parseInt(import.meta.env.VITE_ROUTER_PORT || '8071', 10),

  /** Bekanntes Standardmodell */
  defaultModel: import.meta.env.VITE_DEFAULT_MODEL || 'qwen2.5-coder:1.5b',

  /** Bekanntes großes Modell */
  largeModel: import.meta.env.VITE_LARGE_MODEL || 'qwen2.5-coder:3b',

  /** API-Basis-URL (Dev: /api via Proxy, Prod: direkte URL) */
  apiBaseUrl: import.meta.env.VITE_API_URL || '/api',

  /** Health-Check Polling-Intervall in ms */
  healthInterval: 15_000,

  /** Standard-Timeout für API-Requests in ms */
  defaultTimeout: 10_000,

  /** Timeout für Modellanfragen in ms */
  modelTimeout: 30_000,

  /** UI-Version */
  version: '0.1.0',
} as const;

/** Formatierte Anzeige: Host:Port */
export function routerAddress(): string {
  return `${CONFIG.routerHost}:${CONFIG.routerPort}`;
}
