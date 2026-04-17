import { useEffect } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import { fetchRouteHistory } from '../api/client';
import { useApiCall } from '../hooks/useApi';
import type { RouteHistoryEntry } from '../types';

export function History() {
  const { data, loading, error, execute } = useApiCall<RouteHistoryEntry[]>();

  useEffect(() => {
    execute(() => fetchRouteHistory(100)).catch(() => {});
  }, [execute]);

  const entries = data ?? [];

  return (
    <Layout title="Anfrageverlauf">
      <Card title="Letzte Router-Anfragen" tag="LIVE">
        <div className="btn-group" style={{ marginBottom: '1rem' }}>
          <button
            className="btn btn--sm btn--ghost"
            style={{ marginLeft: 'auto' }}
            onClick={() => execute(() => fetchRouteHistory(100)).catch(() => {})}
            disabled={loading}
          >
            {loading ? 'Lädt…' : 'Aktualisieren'}
          </button>
        </div>

        {error && <div className="alert alert--error">{error}</div>}
        {loading && <span className="text--muted">Lädt…</span>}

        {!loading && !error && (
          <table className="table">
            <thead>
              <tr>
                <th>Zeit</th>
                <th>Client</th>
                <th>Modell</th>
                <th>Fairness</th>
                <th>Status</th>
                <th>Dauer</th>
                <th>Prompt</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.request_id}>
                  <td>{new Date(entry.created_at).toLocaleString('de-DE')}</td>
                  <td>{entry.client_name || 'ohne API-Key'}</td>
                  <td><code>{entry.model || '–'}</code></td>
                  <td>
                    <div className="text--sm">
                      <div>{entry.fairness_risk || 'unknown'}</div>
                      <div className="text--muted">
                        {entry.fairness_review_attempted ? 'Check aktiv' : 'kein Check'}
                        {entry.fairness_review_used ? ' · KI genutzt' : ' · Fallback'}
                        {entry.fairness_review_override ? ' · Override' : ' · kein Override'}
                        {entry.escalation_threshold ? ` · escalation=${entry.escalation_threshold}` : ''}
                      </div>
                    </div>
                  </td>
                  <td>
                    {entry.success ? (
                      <span className="badge badge--ok"><span className="badge__dot" />OK</span>
                    ) : (
                      <span className="badge badge--fail">
                        <span className="badge__dot" />
                        {entry.error_code || 'Fehler'}
                      </span>
                    )}
                  </td>
                  <td>{entry.duration_ms != null ? `${entry.duration_ms} ms` : '–'}</td>
                  <td className="text--muted">{entry.prompt_preview}</td>
                </tr>
              ))}
              {entries.length === 0 && (
                <tr>
                  <td colSpan={7} className="text--muted">Noch keine Route-Anfragen vorhanden.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </Card>
    </Layout>
  );
}
