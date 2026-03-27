import { Card } from '../components/Card';
import { StatusBadge } from '../components/StatusBadge';
import { Layout } from '../components/Layout';
import { CONFIG } from '../config';
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
            <code className="kv__value kv__value--highlight">{CONFIG.defaultModel}</code>
          </div>
          <div className="kv">
            <span className="kv__label">Quelle</span>
            <span className="kv__value">Ollama (lokal)</span>
          </div>
          <p className="text--muted text--sm" style={{ marginTop: '0.75rem' }}>
            Modellwechsel erfordert Backend-Endpunkt GET /models und POST /models/select.
          </p>
        </Card>

        {/* BACKEND ERFORDERLICH: GET /status/service */}
        <Card title="Dienststatus" tag="GEPLANT">
          <div className="kv">
            <span className="kv__label">systemd</span>
            <span className="kv__value text--muted">– Backend fehlt –</span>
          </div>
          <div className="kv">
            <span className="kv__label">Uptime</span>
            <span className="kv__value text--muted">– Backend fehlt –</span>
          </div>
          <div className="kv">
            <span className="kv__label">PID</span>
            <span className="kv__value text--muted">– Backend fehlt –</span>
          </div>
          <p className="text--muted text--sm" style={{ marginTop: '0.75rem' }}>
            Erfordert: GET /status/service
          </p>
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

        <Card title="Backend-Lücken (Phase 1)" tag="INFO">
          <ul className="gap-list">
            <li><code>GET /status/service</code> – Dienststatus</li>
            <li><code>GET /models</code> – Modellliste</li>
            <li><code>POST /models/select</code> – Modellwechsel</li>
            <li><code>GET /settings</code> – Konfiguration lesen</li>
            <li><code>PUT /settings</code> – Konfiguration ändern</li>
            <li><code>GET /logs</code> – Log-Einträge</li>
            <li><code>GET /clients</code> – Client-Verwaltung</li>
          </ul>
        </Card>
      </div>
    </Layout>
  );
}
