import { useState } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import { CONFIG } from '../config';
import type { RouterSettings } from '../types';

/**
 * Router-Einstellungen
 *
 * BACKEND ERFORDERLICH:
 *   - GET /settings – Konfiguration laden
 *   - PUT /settings – Konfiguration speichern
 *
 * Die UI zeigt die erwartete Konfigurationsstruktur.
 * Werte sind Defaults/Annahmen bis GET /settings implementiert ist.
 */

const DEFAULT_SETTINGS: RouterSettings = {
  router_host: '0.0.0.0',
  router_port: CONFIG.routerPort,
  ollama_host: '127.0.0.1',
  ollama_port: 11434,
  timeout: 30,
  default_model: CONFIG.defaultModel,
  logging_level: 'INFO',
  stream_default: false,
};

export function Settings() {
  const [settings, setSettings] = useState<RouterSettings>({ ...DEFAULT_SETTINGS });
  const [saved, setSaved] = useState(false);

  function handleChange(key: keyof RouterSettings, value: string | number | boolean) {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  }

  function handleSave() {
    // BACKEND ERFORDERLICH: PUT /settings
    // Aktuell nur lokaler State, kein persistentes Speichern.
    console.log('[Settings] Würde speichern:', settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  function handleReset() {
    setSettings({ ...DEFAULT_SETTINGS });
    setSaved(false);
  }

  return (
    <Layout title="Router-Einstellungen">
      <div className="alert alert--warn" style={{ marginBottom: '1.5rem' }}>
        <strong>Backend fehlt:</strong> Änderungen werden nur lokal im Browser gehalten.
        Persistentes Speichern erfordert GET /settings und PUT /settings.
      </div>

      <div className="grid grid--2">
        <Card title="Router" tag="GEPLANT">
          <div className="form-group">
            <label className="form-label">Host</label>
            <input
              className="form-input"
              value={settings.router_host}
              onChange={(e) => handleChange('router_host', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Port</label>
            <input
              className="form-input"
              type="number"
              value={settings.router_port}
              onChange={(e) => handleChange('router_port', parseInt(e.target.value) || 0)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Logging-Level</label>
            <select
              className="form-input"
              value={settings.logging_level}
              onChange={(e) => handleChange('logging_level', e.target.value)}
            >
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </div>
        </Card>

        <Card title="Ollama" tag="GEPLANT">
          <div className="form-group">
            <label className="form-label">Host</label>
            <input
              className="form-input"
              value={settings.ollama_host}
              onChange={(e) => handleChange('ollama_host', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Port</label>
            <input
              className="form-input"
              type="number"
              value={settings.ollama_port}
              onChange={(e) => handleChange('ollama_port', parseInt(e.target.value) || 0)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Timeout (Sekunden)</label>
            <input
              className="form-input"
              type="number"
              value={settings.timeout}
              onChange={(e) => handleChange('timeout', parseInt(e.target.value) || 0)}
            />
          </div>
        </Card>
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <Card title="Modell & Verhalten" tag="GEPLANT">
          <div className="grid grid--2">
            <div className="form-group">
              <label className="form-label">Standardmodell</label>
              <input
                className="form-input"
                value={settings.default_model}
                onChange={(e) => handleChange('default_model', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Stream standardmäßig</label>
              <div className="toggle-row">
                <button
                  className={`btn btn--sm ${settings.stream_default ? 'btn--active' : 'btn--ghost'}`}
                  onClick={() => handleChange('stream_default', true)}
                >
                  Ja
                </button>
                <button
                  className={`btn btn--sm ${!settings.stream_default ? 'btn--active' : 'btn--ghost'}`}
                  onClick={() => handleChange('stream_default', false)}
                >
                  Nein
                </button>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div className="btn-group" style={{ marginTop: '1.5rem' }}>
        <button className="btn" onClick={handleSave}>
          Speichern (lokal)
        </button>
        <button className="btn btn--ghost" onClick={handleReset}>
          Zurücksetzen
        </button>
        {saved && <span className="text--ok text--sm" style={{ marginLeft: '1rem' }}>Lokal gespeichert.</span>}
      </div>
    </Layout>
  );
}
