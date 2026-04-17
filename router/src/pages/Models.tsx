import { useState, useEffect } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import { sendRoute, fetchModels, fetchSettings, selectModel, ApiRequestError } from '../api/client';
import { useApiCall } from '../hooks/useApi';
import { CONFIG } from '../config';
import type { OllamaModel, RouteResponse, RouterSettings } from '../types';

export function Models() {
  const [testPrompt, setTestPrompt] = useState('Antworte kurz: Was ist 2+2?');
  const [testResult, setTestResult] = useState<RouteResponse | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [activeModel, setActiveModel] = useState(CONFIG.defaultModel);
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [selectingModel, setSelectingModel] = useState<string | null>(null);

  const { data: models, loading: modelsLoading, error: modelsError, execute } =
    useApiCall<OllamaModel[]>();
  const { execute: loadSettings } = useApiCall<RouterSettings>();

  useEffect(() => {
    execute(fetchModels).catch(() => {});
    loadSettings(fetchSettings)
      .then((settings) => {
        if (settings) setActiveModel(settings.default_model);
      })
      .catch(() => {});
  }, [execute, loadSettings]);

  async function handleTest() {
    setTesting(true);
    setTestError(null);
    setTestResult(null);
    try {
      const res = await sendRoute({ prompt: testPrompt });
      setTestResult(res);
    } catch (err) {
      setTestError(err instanceof ApiRequestError ? err.message : 'Fehler beim Testen');
    } finally {
      setTesting(false);
    }
  }

  async function handleSelectModel(modelName: string) {
    setSelectionError(null);
    setSelectingModel(modelName);
    try {
      const result = await selectModel(modelName);
      setActiveModel(result.model);
    } catch (err) {
      setSelectionError(err instanceof ApiRequestError ? err.message : 'Fehler beim Modellwechsel');
    } finally {
      setSelectingModel(null);
    }
  }

  return (
    <Layout title="Modellverwaltung">
      <div className="grid grid--2">
        {/* Aktives Modell */}
        <Card title="Aktives Modell" tag="LIVE">
          <div className="kv">
            <span className="kv__label">Modell</span>
            <code className="kv__value kv__value--highlight">{activeModel}</code>
          </div>
          <div className="kv">
            <span className="kv__label">Backend</span>
            <span className="kv__value">Ollama</span>
          </div>
        </Card>

        {/* Modellliste */}
        <Card title="Verfügbare Modelle" tag="LIVE">
          {modelsLoading && <span className="text--muted">Lädt…</span>}
          {modelsError && <div className="alert alert--error">{modelsError}</div>}
          {selectionError && <div className="alert alert--error">{selectionError}</div>}
          {!modelsLoading && !modelsError && (
            <table className="table">
              <thead>
                <tr>
                  <th>Modell</th>
                  <th>Größe</th>
                  <th>Status</th>
                  <th>Aktion</th>
                </tr>
              </thead>
              <tbody>
                {(models ?? []).map((m) => (
                  <tr key={m.name}>
                    <td><code>{m.name}</code></td>
                    <td>{m.size}</td>
                    <td>
                      {m.name === activeModel
                        ? <span className="badge badge--ok"><span className="badge__dot" />Aktiv</span>
                        : '–'}
                    </td>
                    <td>
                      <button
                        className="btn btn--sm btn--ghost"
                        onClick={() => handleSelectModel(m.name)}
                        disabled={selectingModel === m.name || m.name === activeModel}
                      >
                        {selectingModel === m.name ? 'Speichert…' : m.name === activeModel ? 'Aktiv' : 'Aktivieren'}
                      </button>
                    </td>
                  </tr>
                ))}
                {(models ?? []).length === 0 && (
                  <tr>
                    <td colSpan={4} className="text--muted">Keine Modelle gefunden.</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </Card>
      </div>

      {/* Modelltest – SOFORT NUTZBAR */}
      <div style={{ marginTop: '1.5rem' }}>
        <Card title="Modelltest" tag="LIVE">
          <div className="form-group">
            <label className="form-label">Prompt</label>
            <textarea
              className="form-input form-input--textarea"
              rows={3}
              value={testPrompt}
              onChange={(e) => setTestPrompt(e.target.value)}
              placeholder="Prompt eingeben..."
            />
          </div>
          <button
            className="btn"
            onClick={handleTest}
            disabled={testing || !testPrompt.trim()}
          >
            {testing ? 'Sende…' : 'An Modell senden'}
          </button>

          {testResult && (
            <div className="result-box" style={{ marginTop: '1rem' }}>
              <div className="kv">
                <span className="kv__label">Modell</span>
                <code className="kv__value">{testResult.model}</code>
              </div>
              <div className="kv">
                <span className="kv__label">Status</span>
                <span className="kv__value">{testResult.done ? 'Fertig' : 'Läuft…'}</span>
              </div>
            <div className="kv">
              <span className="kv__label">Grund</span>
              <span className="kv__value">{testResult.done_reason}</span>
            </div>
            <div className="kv">
              <span className="kv__label">Fairness-Check</span>
              <span className="kv__value">
                {testResult.fairness_review_attempted ? 'KI eingebunden' : 'nicht ausgeführt'}
              </span>
            </div>
            {testResult.fairness_review_attempted && (
              <>
                <div className="kv">
                  <span className="kv__label">Fairness-Risiko</span>
                  <span className="kv__value">{testResult.fairness_risk || 'unknown'}</span>
                </div>
                <div className="kv">
                  <span className="kv__label">Route angehoben</span>
                  <span className="kv__value">
                    {testResult.fairness_review_override ? 'Ja' : 'Nein'}
                  </span>
                </div>
              </>
            )}
            <div style={{ marginTop: '0.75rem' }}>
              <label className="form-label">Antwort</label>
              <pre className="code-block">{testResult.response}</pre>
            </div>
            </div>
          )}

          {testError && (
            <div className="alert alert--error" style={{ marginTop: '1rem' }}>
              {testError}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
}
