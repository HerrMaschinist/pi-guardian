export const CONFIG = {
  appName: 'PI Guardian',
  appSubtitle: 'Operational control surface',
  apiBaseUrl: import.meta.env.VITE_GUARDIAN_API_PREFIX || '/api/guardian',
  apiTarget: import.meta.env.VITE_GUARDIAN_API_TARGET || 'http://127.0.0.1:8000',
  refreshIntervalMs: Number(import.meta.env.VITE_GUARDIAN_REFRESH_INTERVAL_MS || '20000'),
  historyLimit: Number(import.meta.env.VITE_GUARDIAN_HISTORY_LIMIT || '8'),
  version: '0.1.0',
} as const;
