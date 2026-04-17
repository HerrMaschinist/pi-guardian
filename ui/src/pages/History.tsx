import { useEffect, useMemo, useState } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import { ApiRequestError, fetchRouteHistory } from '../api/client';
import type { RouteHistoryEntry } from '../types';

function pickValue(entry: RouteHistoryEntry, keys: string[]) {
  for (const key of keys) {
    const value = entry[key];
    if (value !== undefined && value !== null && value !== '') return String(value);
  }
  return '–';
}

export function History() {
  const [entries, setEntries] = useState<RouteHistoryEntry[]>([]);
  const [limit, setLimit] = useState(25);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshedAt, setRefreshedAt] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const nextEntries = await fetchRouteHistory(limit);
      setEntries(nextEntries);
      setRefreshedAt(new Date().toLocaleTimeString('de-DE'));
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : 'Verlauf konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [limit]);

  const hasAuthorizationIssue = useMemo(() => {
    return Boolean(error && /401|403|Unauthorized|nicht nutzen/i.test(error));
  }, [error]);

  return (
    <Layout title="History">
      <div className="grid grid--dense">
        <Card title="Verlauf" tag="API">
          <div className="kv">
            <span className="kv__label">Einträge</span>
            <span className="kv__value">{entries.length}</span>
          </div>
          <div className="kv">
            <span className="kv__label">Letztes Update</span>
            <span className="kv__value">{refreshedAt ?? '–'}</span>
          </div>
          <button className="btn btn--sm" onClick={() => void load()} disabled={loading}>
            {loading ? 'Lade…' : 'Neu laden'}
          </button>
        </Card>

        <Card title="Anzeige" tag="FILTER">
          <div className="form-group">
            <label className="form-label">Limit</label>
            <input
              className="form-input"
              type="number"
              min={1}
              max={200}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value) || 25)}
            />
          </div>
          <p className="text--muted text--sm">
            Die Ansicht greift auf `/history` zu. Falls dein API-Key diese Route nicht darf,
            wird die Seite den Fehler klar anzeigen.
          </p>
        </Card>

        <Card title="Browser-Hinweis" tag="AUTH">
          <p className="text--sm">
            Die Seite nutzt denselben gespeicherten Router API-Key wie die restliche UI.
            Wenn der Zugriff auf `history` gesperrt ist, brauchst du einen Schlüssel mit
            entsprechender Freigabe.
          </p>
        </Card>
      </div>

      {error && (
        <div className={`alert ${hasAuthorizationIssue ? 'alert--warn' : 'alert--error'}`} style={{ marginTop: '1.5rem' }}>
          <strong>Fehler:</strong> {error}
        </div>
      )}

      <div className="section">
        <Card title="Request History" tag="API">
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Zeit</th>
                  <th>Anfrage</th>
                  <th>Client</th>
                  <th>Fehler</th>
                  <th>Modell</th>
                  <th>Dauer</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry, index) => (
                  <tr key={`${pickValue(entry, ['request_id', 'id', 'timestamp'])}-${index}`}>
                    <td>{pickValue(entry, ['created_at', 'timestamp'])}</td>
                    <td>
                      <strong>{pickValue(entry, ['prompt_preview'])}</strong>
                      <div className="text--muted text--sm">
                        {pickValue(entry, ['client_name'])}
                        {entry.fairness_risk ? ` · ${entry.fairness_risk}` : ''}
                      </div>
                    </td>
                    <td>{pickValue(entry, ['client_name'])}</td>
                    <td>{pickValue(entry, ['error_code'])}</td>
                    <td>{pickValue(entry, ['model'])}</td>
                    <td>{pickValue(entry, ['duration_ms'])}</td>
                  </tr>
                ))}
                {entries.length === 0 && !loading && (
                  <tr>
                    <td colSpan={6} className="text--muted" style={{ textAlign: 'center' }}>
                      Keine Verlaufsdaten vorhanden oder Zugriff verweigert.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </Layout>
  );
}
