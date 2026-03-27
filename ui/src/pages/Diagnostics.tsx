import { useState } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import { fetchHealth, sendRoute, ApiRequestError } from '../api/client';
import { routerAddress, CONFIG } from '../config';
import type { HealthResponse, RouteRequest, RouteResponse, ConnectionState } from '../types';

interface Props {
  connectionState: ConnectionState;
  onRefresh: () => void;
}

/**
 * Diagnose-Seite
 *
 * SOFORT NUTZBAR:
 *   - Health-Check (GET /health)
 *   - Route-Test mit Prompt (POST /route)
 *   - Request/Response-Anzeige
 *   - Fehleranzeige
 */
export function Diagnostics({ connectionState, onRefresh }: Props) {
  // Health-Check State
  const [healthResult, setHealthResult] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthTime, setHealthTime] = useState<number | null>(null);

  // Route-Test State
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('');
  const [routeResult, setRouteResult] = useState<RouteResponse | null>(null);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeTime, setRouteTime] = useState<number | null>(null);
  const [lastRequest, setLastRequest] = useState<string | null>(null);

  async function handleHealthCheck() {
    setHealthLoading(true);
    setHealthError(null);
    setHealthResult(null);
    const start = performance.now();
    try {
      const res = await fetchHealth();
      setHealthTime(Math.round(performance.now() - start));
      setHealthResult(res);
      onRefresh();
    } catch (err) {
      setHealthTime(Math.round(performance.now() - start));
      setHealthError(err instanceof ApiRequestError ? err.message : 'Unbekannter Fehler');
    } finally {
      setHealthLoading(false);
    }
  }

  async function handleRouteTest() {
    if (!prompt.trim()) return;
    setRouteLoading(true);
    setRouteError(null);
    setRouteResult(null);

    const requestBody: RouteRequest = { prompt: prompt.trim() };
    if (model.trim()) requestBody.preferred_model = model.trim();
    setLastRequest(JSON.stringify(requestBody, null, 2));

    const start = performance.now();
    try {
      const res = await sendRoute(requestBody);
      setRouteTime(Math.round(performance.now() - start));
      setRouteResult(res);
    } catch (err) {
      setRouteTime(Math.round(performance.now() - start));
      setRouteError(err instanceof ApiRequestError ? err.message : 'Unbekannter Fehler');
    } finally {
      setRouteLoading(false);
    }
  }

  return (
    <Layout title="Test & Diagnose">
      <div className="grid grid--2">
        {/* Health-Check */}
        <Card title="Health-Check" tag="LIVE">
          <p className="text--sm">Prüft GET /health auf dem Router.</p>
          <button
            className="btn"
            onClick={handleHealthCheck}
            disabled={healthLoading}
            style={{ marginTop: '0.5rem' }}
          >
            {healthLoading ? 'Prüfe…' : 'Health-Check ausführen'}
          </button>

          {healthResult && (
            <div className="result-box" style={{ marginTop: '1rem' }}>
              <div className="kv">
                <span className="kv__label">Status</span>
                <code className="kv__value kv__value--highlight">{healthResult.status}</code>
              </div>
              <div className="kv">
                <span className="kv__label">Antwortzeit</span>
                <span className="kv__value">{healthTime} ms</span>
              </div>
            </div>
          )}
          {healthError && (
            <div className="alert alert--error" style={{ marginTop: '1rem' }}>
              <strong>Fehler:</strong> {healthError}
              {healthTime !== null && <span className="text--sm"> ({healthTime} ms)</span>}
            </div>
          )}
        </Card>

        {/* Verbindungsübersicht */}
        <Card title="Verbindungsstatus" tag="LIVE">
          <div className="kv">
            <span className="kv__label">Ziel</span>
            <code className="kv__value">{routerAddress()}</code>
          </div>
          <div className="kv">
            <span className="kv__label">Proxy</span>
            <code className="kv__value">/api → Backend</code>
          </div>
          <div className="kv">
            <span className="kv__label">Zustand</span>
            <span className={`kv__value ${connectionState === 'connected' ? 'text--ok' : 'text--fail'}`}>
              {connectionState === 'connected' ? 'Erreichbar' : connectionState === 'checking' ? 'Prüfe…' : 'Nicht erreichbar'}
            </span>
          </div>
        </Card>
      </div>

      {/* Route-Test */}
      <div style={{ marginTop: '1.5rem' }}>
        <Card title="Route-Test" tag="LIVE">
          <div className="grid grid--2">
            <div className="form-group">
              <label className="form-label">Prompt</label>
              <textarea
                className="form-input form-input--textarea"
                rows={4}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="z.B. Sage Hallo in einem Satz."
              />
            </div>
            <div>
              <div className="form-group">
                <label className="form-label">Modell (optional)</label>
                <input
                  className="form-input"
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder={`Standard: ${CONFIG.defaultModel}`}
                />
              </div>
              <button
                className="btn"
                onClick={handleRouteTest}
                disabled={routeLoading || !prompt.trim()}
                style={{ marginTop: '0.5rem' }}
              >
                {routeLoading ? 'Sende…' : 'POST /route senden'}
              </button>
            </div>
          </div>

          {/* Request anzeigen */}
          {lastRequest && (
            <div style={{ marginTop: '1rem' }}>
              <label className="form-label">Request Body</label>
              <pre className="code-block code-block--request">{lastRequest}</pre>
            </div>
          )}

          {/* Response anzeigen */}
          {routeResult && (
            <div className="result-box" style={{ marginTop: '1rem' }}>
              <div className="kv">
                <span className="kv__label">Modell</span>
                <code className="kv__value">{routeResult.model}</code>
              </div>
              <div className="kv">
                <span className="kv__label">Status</span>
                <span className="kv__value">{routeResult.done ? 'Abgeschlossen' : 'Läuft…'}</span>
              </div>
              <div className="kv">
                <span className="kv__label">Grund</span>
                <span className="kv__value">{routeResult.done_reason}</span>
              </div>
              <div className="kv">
                <span className="kv__label">Antwortzeit</span>
                <span className="kv__value">{routeTime} ms</span>
              </div>
              <div style={{ marginTop: '0.75rem' }}>
                <label className="form-label">Response</label>
                <pre className="code-block">{routeResult.response}</pre>
              </div>
            </div>
          )}

          {routeError && (
            <div className="alert alert--error" style={{ marginTop: '1rem' }}>
              <strong>Fehler:</strong> {routeError}
              {routeTime !== null && <span className="text--sm"> ({routeTime} ms)</span>}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
}
