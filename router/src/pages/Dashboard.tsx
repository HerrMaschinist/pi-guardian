import { useEffect } from 'react';
import { Card } from '../components/Card';
import { StatusBadge } from '../components/StatusBadge';
import { Layout } from '../components/Layout';
import { CONFIG } from '../config';
import { fetchServiceStatus, fetchSettings } from '../api/client';
import { useApiCall } from '../hooks/useApi';
import type { ConnectionState, RouterSettings, ServiceStatus } from '../types';

interface Props {
  connectionState: ConnectionState;
  lastCheck: string | null;
  healthError: string | null;
  onRefresh: () => void;
}

export function Dashboard({ connectionState, lastCheck, healthError, onRefresh }: Props) {
  const { data: serviceStatus, loading: statusLoading, error: statusError, execute } =
    useApiCall<ServiceStatus>();
  const {
    data: routerSettings,
    loading: settingsLoading,
    error: settingsError,
    execute: loadSettings,
  } = useApiCall<RouterSettings>();

  useEffect(() => {
    execute(fetchServiceStatus).catch(() => {});
    loadSettings(fetchSettings).catch(() => {});
  }, [execute, loadSettings]);

  return (
    <Layout title="Systemübersicht">
      <div className="grid grid--3">
        {/* SOFORT NUTZBAR */}
        <Card title="Router-Status" tag="LIVE">
          <div className="kv">
            <span className="kv__label">Backend</span>
            <StatusBadge state={connectionState} />
          </div>
          <div className="kv">
            <span className="kv__label">Host</span>
            <code className="kv__value">{CONFIG.routerHost}</code>
          </div>
          <div className="kv">
            <span className="kv__label">Port</span>
            <code className="kv__value">{CONFIG.routerPort}</code>
          </div>
          <div className="kv">
            <span className="kv__label">Letzter Check</span>
            <span className="kv__value">{lastCheck ?? '–'}</span>
          </div>
          {healthError && (
            <div className="alert alert--error">{healthError}</div>
          )}
          <button className="btn btn--sm" onClick={onRefresh}>
            Health prüfen
          </button>
        </Card>

        {/* SOFORT NUTZBAR (statischer Wert, bekannt aus Kontext) */}
        <Card title="Aktives Modell" tag="LIVE">
          <div className="kv">
            <span className="kv__label">Standardmodell</span>
            <code className="kv__value kv__value--highlight">
              {routerSettings?.default_model || CONFIG.defaultModel}
            </code>
          </div>
          <div className="kv">
            <span className="kv__label">Quelle</span>
            <span className="kv__value">Ollama (lokal)</span>
          </div>
          <div className="kv">
            <span className="kv__label">Timeout</span>
            <span className="kv__value">
              {settingsLoading ? 'Lädt…' : `${routerSettings?.timeout ?? CONFIG.modelTimeout / 1000}s`}
            </span>
          </div>
          {settingsError && (
            <div className="alert alert--error">{settingsError}</div>
          )}
          <p className="text--muted text--sm" style={{ marginTop: '0.75rem' }}>
            Modellliste kommt aus GET /models. Das Standardmodell kann jetzt über
            POST /models/select umgeschaltet werden.
          </p>
        </Card>

        {/* GET /status/service */}
        <Card title="Dienststatus" tag="LIVE">
          {statusLoading && (
            <span className="text--muted">Lädt…</span>
          )}
          {statusError && !statusLoading && (
            <div className="alert alert--error">{statusError}</div>
          )}
          {serviceStatus && !statusLoading && (
            <>
              <div className="kv">
                <span className="kv__label">systemd</span>
                <StatusBadge
                  state={serviceStatus.active ? 'connected' : 'disconnected'}
                  label={serviceStatus.active ? 'Aktiv' : 'Inaktiv'}
                />
              </div>
              <div className="kv">
                <span className="kv__label">Uptime</span>
                <span className="kv__value">{serviceStatus.uptime ?? '–'}</span>
              </div>
              <div className="kv">
                <span className="kv__label">PID</span>
                <code className="kv__value">{serviceStatus.pid ?? '–'}</code>
              </div>
              <div className="kv">
                <span className="kv__label">CPU</span>
                <span className="kv__value">
                  {serviceStatus.cpu_percent != null ? `${serviceStatus.cpu_percent} %` : '–'}
                </span>
              </div>
              <div className="kv">
                <span className="kv__label">Memory</span>
                <span className="kv__value">{serviceStatus.memory_usage ?? '–'}</span>
              </div>
            </>
          )}
        </Card>
      </div>

      {/* Schnellaktionen */}
      <div className="grid grid--2" style={{ marginTop: '1.5rem' }}>
        <Card title="Schnelltest" tag="LIVE">
          <p className="text--sm">
            Über „Diagnose" kannst du direkt einen Prompt an den Router senden
            und die Antwort prüfen.
          </p>
        </Card>

        <Card title="Aktueller API-Stand" tag="INFO">
          <ul className="gap-list">
            <li><code>GET /health</code>, <code>GET /status/service</code>, <code>GET /logs</code> – vorhanden</li>
            <li><code>GET /models</code>, <code>GET /settings</code>, <code>POST /route</code> – vorhanden, hängen teils an Ollama</li>
            <li><code>/clients</code> – CRUD ist vorhanden</li>
            <li><code>PUT /settings</code> und <code>POST /models/select</code> – vorhanden</li>
          </ul>
        </Card>
      </div>
    </Layout>
  );
}
