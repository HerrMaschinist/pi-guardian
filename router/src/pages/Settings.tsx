import { useState, useEffect } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import {
  fetchSettings,
  updateSettings,
  ApiRequestError,
  getStoredRouterApiKey,
  setStoredRouterApiKey,
} from '../api/client';
import { useApiCall } from '../hooks/useApi';
import { CONFIG } from '../config';
import type { RouterSettings, SettingsUpdateResponse } from '../types';

const DEFAULT_SETTINGS: RouterSettings = {
  router_host: '127.0.0.1',
  router_port: CONFIG.routerPort,
  ollama_host: '127.0.0.1',
  ollama_port: 11434,
  timeout: 120,
  default_model: CONFIG.defaultModel,
  logging_level: 'INFO',
  stream_default: false,
  require_api_key: false,
  escalation_threshold: 'medium',
};

export function Settings() {
  const [settings, setSettings] = useState<RouterSettings>({ ...DEFAULT_SETTINGS });
  const [routerApiKey, setRouterApiKey] = useState(() => getStoredRouterApiKey());
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [restartService, setRestartService] = useState(false);
  const [saveInfo, setSaveInfo] = useState<string | null>(null);
  const [needsApiKey, setNeedsApiKey] = useState(() => !getStoredRouterApiKey());

  const { loading, error, execute } = useApiCall<RouterSettings>();

  useEffect(() => {
    setNeedsApiKey(false);
    execute(fetchSettings).then((result) => {
      if (result) setSettings(result);
    }).catch(() => {
      setNeedsApiKey(true);
    });
  }, [execute, routerApiKey]);

  function handleChange(key: keyof RouterSettings, value: string | number | boolean) {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
    setSaveError(null);
    setSaveInfo(null);
  }

  function handleApiKeyChange(value: string) {
    setRouterApiKey(value);
    setStoredRouterApiKey(value);
    setNeedsApiKey(!value.trim());
    setSaved(false);
    setSaveError(null);
    setSaveInfo(null);
  }

  async function handleSave() {
    setSaveError(null);
    setSaveInfo(null);
    try {
      const updated: SettingsUpdateResponse = await updateSettings({
        ...settings,
        restart_service: restartService,
      });
      setSettings(updated.settings);
      setSaved(true);
      setSaveInfo(
        updated.restart_requested
          ? updated.restart_performed
            ? updated.restart_message || 'Einstellungen gespeichert und Dienst neu gestartet.'
            : updated.restart_message || 'Einstellungen gespeichert, Dienstneustart aber nicht ausgeführt.'
          : 'Einstellungen gespeichert.'
      );
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setSaveError(err instanceof ApiRequestError ? err.message : 'Speichern fehlgeschlagen');
    }
  }

  function handleReset() {
    setSettings({ ...DEFAULT_SETTINGS });
    setSaved(false);
    setSaveError(null);
    setSaveInfo(null);
  }

  return (
    <Layout title="Router-Einstellungen">
      <div className="alert alert--warn" style={{ marginBottom: '1.5rem' }}>
        <strong>Hinweis:</strong> Änderungen werden sofort in die Router-`.env`
        geschrieben. Die Admin-Session wird serverseitig wiederhergestellt und
        optional kann ein Dienstneustart direkt mit angefordert werden.
      </div>

      {needsApiKey && (
        <div className="alert alert--warn" style={{ marginBottom: '1.5rem' }}>
          Die Admin-Session konnte nicht automatisch wiederhergestellt werden.
          Du kannst hier optional einen manuellen Admin-API-Key hinterlegen.
        </div>
      )}

      {error && (
        <div className="alert alert--error" style={{ marginBottom: '1.5rem' }}>
          Einstellungen konnten nicht geladen werden: {error}
        </div>
      )}

      {saveError && (
        <div className="alert alert--error" style={{ marginBottom: '1.5rem' }}>
          Einstellungen konnten nicht gespeichert werden: {saveError}
        </div>
      )}

      {saveInfo && (
        <div className="alert alert--ok" style={{ marginBottom: '1.5rem' }}>
          {saveInfo}
        </div>
      )}

      {loading && <span className="text--muted" style={{ marginBottom: '1.5rem', display: 'block' }}>Lädt…</span>}

      <div className="grid grid--2">
        <Card title="Router" tag="LIVE">
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

        <Card title="Ollama" tag="LIVE">
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
        <Card title="Modell & Verhalten" tag="LIVE">
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
            <div className="form-group">
              <label className="form-label">API-Key für /route erforderlich</label>
              <div className="toggle-row">
                <button
                  className={`btn btn--sm ${settings.require_api_key ? 'btn--active' : 'btn--ghost'}`}
                  onClick={() => handleChange('require_api_key', true)}
                >
                  Ja
                </button>
                <button
                  className={`btn btn--sm ${!settings.require_api_key ? 'btn--active' : 'btn--ghost'}`}
                  onClick={() => handleChange('require_api_key', false)}
                >
                  Nein
                </button>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Eskalations-Schwelle</label>
              <select
                className="form-input"
                value={settings.escalation_threshold}
                onChange={(e) => handleChange('escalation_threshold', e.target.value)}
              >
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
              <small className="text--muted">
                Ab dieser Risikostufe schaltet der Router automatisch auf das größere Modell um.
              </small>
            </div>
          </div>
        </Card>
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <Card title="Admin-Zugriff" tag="LIVE">
          <div className="form-group">
            <label className="form-label">Router-API-Key für geschützte Requests</label>
            <input
              className="form-input"
              type="password"
              value={routerApiKey}
              onChange={(e) => handleApiKeyChange(e.target.value)}
              placeholder="API-Key eintragen"
              autoComplete="off"
              spellCheck={false}
            />
            <small className="text--muted">
              Wird lokal im Browser gespeichert und automatisch als <code>X-API-Key</code> gesendet.
            </small>
          </div>
        </Card>
      </div>

      <div className="btn-group" style={{ marginTop: '1.5rem' }}>
        <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <input
            type="checkbox"
            checked={restartService}
            onChange={(e) => setRestartService(e.target.checked)}
          />
          Dienst nach dem Speichern neu starten
        </label>
        <button className="btn" onClick={handleSave}>
          Einstellungen speichern
        </button>
        <button className="btn btn--ghost" onClick={handleReset}>
          Zurücksetzen
        </button>
        {saved && <span className="text--ok text--sm" style={{ marginLeft: '1rem' }}>Lokal gespeichert.</span>}
      </div>
    </Layout>
  );
}
