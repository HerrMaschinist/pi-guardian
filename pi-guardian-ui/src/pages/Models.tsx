import { useState } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import { sendRoute, ApiRequestError } from '../api/client';
import { CONFIG } from '../config';
import type { RouteResponse } from '../types';

/**
 * Modellverwaltung
 *
 * SOFORT NUTZBAR:
 *   - Testanfrage an das aktive Modell über POST /route
 *
 * BACKEND ERFORDERLICH:
 *   - Modellliste (GET /models)
 *   - Modellwechsel (POST /models/select)
 */
export function Models() {
  const [testPrompt, setTestPrompt] = useState('Antworte kurz: Was ist 2+2?');
  const [testResult, setTestResult] = useState<RouteResponse | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  // Bekanntes Modell (aus Config, bis GET /models verfügbar)
  const currentModel = CONFIG.defaultModel;

  // MOCK: Modellliste – wird durch GET /models ersetzt
  const mockModels = [
    { name: CONFIG.defaultModel, size: '~930 MB', active: true },
  ];

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

  return (
    <Layout title="Modellverwaltung">
      <div className="grid grid--2">
        {/* Aktives Modell */}
        <Card title="Aktives Modell" tag="LIVE">
          <div className="kv">
            <span className="kv__label">Modell</span>
            <code className="kv__value kv__value--highlight">{currentModel}</code>
          </div>
          <div className="kv">
            <span className="kv__label">Backend</span>
            <span className="kv__value">Ollama</span>
          </div>
        </Card>

        {/* Modellliste – BACKEND ERFORDERLICH */}
        <Card title="Verfügbare Modelle" tag="GEPLANT">
          <table className="table">
            <thead>
              <tr>
                <th>Modell</th>
                <th>Größe</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {mockModels.map((m) => (
                <tr key={m.name}>
                  <td><code>{m.name}</code></td>
                  <td>{m.size}</td>
                  <td>{m.active ? <span className="badge badge--ok"><span className="badge__dot" />Aktiv</span> : '–'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text--muted text--sm" style={{ marginTop: '0.75rem' }}>
            Vollständige Modellliste erfordert: GET /models.
            Modellwechsel erfordert: POST /models/select.
          </p>
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
