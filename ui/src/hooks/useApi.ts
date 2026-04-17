import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchHealth, ApiRequestError } from '../api/client';
import { CONFIG } from '../config';
import type { ConnectionState, HealthResponse } from '../types';

/**
 * Hook: Periodischer Health-Check gegen GET /health.
 * SOFORT NUTZBAR.
 */
export function useHealthCheck(intervalMs = CONFIG.healthInterval) {
  const [state, setState] = useState<ConnectionState>('checking');
  const [lastCheck, setLastCheck] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<HealthResponse | null>(null);
  const mountedRef = useRef(true);

  const check = useCallback(async () => {
    if (!mountedRef.current) return;
    setState('checking');
    try {
      const res = await fetchHealth();
      if (!mountedRef.current) return;
      setData(res);
      if (res.status === 'ok' || res.status === 'degraded') {
        setState('connected');
        setError(
          res.status === 'degraded' ? 'Router erreichbar, Backend teilweise degradiert.' : null
        );
      } else {
        setState('error');
        setError(`Unerwarteter Status: ${res.status}`);
      }
    } catch (err) {
      if (!mountedRef.current) return;
      setState('disconnected');
      setError(err instanceof ApiRequestError ? err.message : 'Verbindung fehlgeschlagen');
    }
    setLastCheck(new Date().toLocaleTimeString('de-DE'));
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    check();
    const id = setInterval(check, intervalMs);
    return () => {
      mountedRef.current = false;
      clearInterval(id);
    };
  }, [check, intervalMs]);

  return { state, lastCheck, error, data, refresh: check };
}

/**
 * Hook: Generischer async-Aufruf mit Loading/Error-State.
 */
export function useApiCall<T>() {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (fn: () => Promise<T>) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setData(result);
      return result;
    } catch (err) {
      const msg = err instanceof ApiRequestError ? err.message : 'Fehler';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}
