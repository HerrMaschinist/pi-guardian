import { useState, useEffect } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import { fetchLogs } from '../api/client';
import { useApiCall } from '../hooks/useApi';
import type { LogEntry } from '../types';

const LEVEL_CLASS: Record<LogEntry['level'], string> = {
  info: 'log__level--info',
  warn: 'log__level--warn',
  error: 'log__level--error',
};

export function Logs() {
  const [filter, setFilter] = useState<'all' | LogEntry['level']>('all');
  const { data: logs, loading, error, execute } = useApiCall<LogEntry[]>();

  useEffect(() => {
    execute(() => fetchLogs(200)).catch(() => {});
  }, [execute]);

  const entries = logs ?? [];
  const filtered = filter === 'all' ? entries : entries.filter((l) => l.level === filter);

  return (
    <Layout title="Logs & Ereignisse">
      <Card title="Letzte Ereignisse" tag="LIVE">
        <div className="btn-group" style={{ marginBottom: '1rem' }}>
          {(['all', 'info', 'warn', 'error'] as const).map((level) => (
            <button
              key={level}
              className={`btn btn--sm ${filter === level ? 'btn--active' : 'btn--ghost'}`}
              onClick={() => setFilter(level)}
            >
              {level === 'all' ? 'Alle' : level.toUpperCase()}
            </button>
          ))}
          <button
            className="btn btn--sm btn--ghost"
            style={{ marginLeft: 'auto' }}
            onClick={() => execute(() => fetchLogs(200)).catch(() => {})}
            disabled={loading}
          >
            {loading ? 'Lädt…' : 'Aktualisieren'}
          </button>
        </div>

        {error && <div className="alert alert--error">{error}</div>}

        {loading && <span className="text--muted">Lädt…</span>}

        {!loading && !error && (
          <div className="log-list">
            {filtered.map((entry, i) => (
              <div key={i} className="log-entry">
                <span className="log__time">
                  {new Date(entry.timestamp).toLocaleTimeString('de-DE')}
                </span>
                <span className={`log__level ${LEVEL_CLASS[entry.level]}`}>
                  {entry.level.toUpperCase()}
                </span>
                <span className="log__source">{entry.source}</span>
                <span className="log__msg">{entry.message}</span>
              </div>
            ))}
            {filtered.length === 0 && (
              <p className="text--muted">Keine Einträge für diesen Filter.</p>
            )}
          </div>
        )}
      </Card>
    </Layout>
  );
}
