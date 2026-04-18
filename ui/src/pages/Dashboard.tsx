import { useEffect, useState } from 'react';
import { Card } from '../components/Card';
import { StatusBadge } from '../components/StatusBadge';
import { Layout } from '../components/Layout';
import { ApiRequestError, fetchServiceStatus, fetchSettings } from '../api/client';
import { CONFIG } from '../config';
import type { RouterSettings, ServiceStatus } from '../types';
import type { ConnectionState } from '../types';

interface Props {
  connectionState: ConnectionState;
  lastCheck: string | null;
  healthError: string | null;
  onRefresh: () => void;
}

/**
 * Dashboard – Systemübersicht
 *
 * SOFORT NUTZBAR:
 *   - Health-Status, Verbindungsanzeige, letzter Check
 *
 * BACKEND ERFORDERLICH:
 *   - Dienststatus (GET /status/service)
 *   - Modellinfo (GET /models)
 *   - Systemmetriken (CPU, RAM, Temp)
 */
export function Dashboard({ connectionState, lastCheck, healthError, onRefresh }: Props) {
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus | null>(null);
  const [serviceStatusError, setServiceStatusError] = useState<string | null>(null);
  const [serviceStatusLoading, setServiceStatusLoading] = useState(false);
  const [routerSettings, setRouterSettings] = useState<RouterSettings | null>(null);
  const cpuPercent = serviceStatus?.cpu_percent;

  async function loadServiceStatus() {
    setServiceStatusLoading(true);
    setServiceStatusError(null);
    try {
      const result = await fetchServiceStatus();
      setServiceStatus(result);
    } catch (err) {
      setServiceStatusError(err instanceof ApiRequestError ? err.message : 'Dienststatus konnte nicht geladen werden.');
    } finally {
      setServiceStatusLoading(false);
    }
  }

  async function loadRouterSettings() {
    try {
      const result = await fetchSettings();
      setRouterSettings(result);
    } catch {
      setRouterSettings(null);
    }
  }

  useEffect(() => {
    void loadServiceStatus();
    void loadRouterSettings();
  }, []);

  function handleRefresh() {
    onRefresh();
    void loadServiceStatus();
  }

  return (
    <Layout title="Systemübersicht">
      <div className="grid grid--dense">
        <Card title="Router-Kanal" tag="CONTROL">
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
            <span className="kv__label">Backend-API</span>
            <code className="kv__value">/api</code>
          </div>
          <div className="kv">
            <span className="kv__label">Letzter Check</span>
            <span className="kv__value">{lastCheck ?? '–'}</span>
          </div>
          {healthError && (
            <div className="alert alert--error">{healthError}</div>
          )}
          <button className="btn btn--sm" onClick={handleRefresh} disabled={serviceStatusLoading}>
            Health prüfen
          </button>
        </Card>

        <Card title="Model Lane" tag="EXEC">
          <div className="kv">
            <span className="kv__label">Fast Model</span>
            <code className="kv__value kv__value--highlight">
              {routerSettings?.default_model ?? CONFIG.defaultModel}
            </code>
          </div>
          <div className="kv">
            <span className="kv__label">Deep Model</span>
            <code className="kv__value kv__value--highlight">
              {routerSettings?.large_model ?? CONFIG.largeModel}
            </code>
          </div>
          <p className="text--muted text--sm" style={{ marginTop: '0.75rem' }}>
            Die Konfiguration stammt jetzt aus GET /settings und ergänzt die installierten
            Modelle aus GET /models.
          </p>
        </Card>

        <Card title="Service Monitor" tag="OPS">
          <div className="kv">
            <span className="kv__label">systemd</span>
            <span className={`kv__value ${serviceStatus?.active ? 'text--ok' : 'text--fail'}`}>
              {serviceStatus ? (serviceStatus.active ? 'Aktiv' : 'Inaktiv') : '–'}
            </span>
          </div>
          <div className="kv">
            <span className="kv__label">Uptime</span>
            <span className="kv__value">{serviceStatus?.uptime ?? '–'}</span>
          </div>
          <div className="kv">
            <span className="kv__label">PID</span>
            <span className="kv__value">{serviceStatus?.pid ?? '–'}</span>
          </div>
          <div className="kv">
            <span className="kv__label">Speicher</span>
            <span className="kv__value">{serviceStatus?.memory_usage ?? '–'}</span>
          </div>
          <div className="kv">
            <span className="kv__label">CPU</span>
            <span className="kv__value">
              {cpuPercent !== null && cpuPercent !== undefined
                ? `${cpuPercent.toFixed(1)} %`
                : '–'}
            </span>
          </div>
          <p className="text--muted text--sm" style={{ marginTop: '0.75rem' }}>
            Erfordert: GET /status/service
          </p>
          {serviceStatusError && (
            <div className="alert alert--warn" style={{ marginTop: '0.75rem' }}>
              {serviceStatusError}
            </div>
          )}
        </Card>

        <Card title="Execution Lanes" tag="ROUTING">
          <div className="trace-list">
            <div className="trace-list__row">
              <span className="trace-list__label">`llm_only`</span>
              <span className="trace-list__value">Direkt über Modellpfad mit Fairness-Prüfung</span>
            </div>
            <div className="trace-list__row">
              <span className="trace-list__label">`tool_required`</span>
              <span className="trace-list__value">Kontrollierte Read-Only-Tools im `/route`-Pfad</span>
            </div>
            <div className="trace-list__row">
              <span className="trace-list__label">`internet_required`</span>
              <span className="trace-list__value">Erkannt, aber bewusst noch nicht produktiv verdrahtet</span>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid--2 section">
        <Card title="Operator Console" tag="DIAG">
          <p className="text--sm">
            Die Diagnose-Seite zeigt jetzt nicht nur Prompt und Antwort, sondern auch
            Decision-Klassifikation, Policy-Trace und tatsächliche Tool-Ausführung.
          </p>
        </Card>

        <Card title="Bewusst offen" tag="PENDING">
          <ul className="gap-list">
            <li><code>internet_required</code> bleibt vorerst ein kontrollierter Stop statt Blindzugriff</li>
            <li>Normale `/route`-Tool-Ausführung ist bewusst klein gehalten und nicht agentisch</li>
            <li>UI bleibt Systemkonsole, kein generisches AI-Prompt-Dashboard</li>
          </ul>
        </Card>
      </div>
    </Layout>
  );
}
