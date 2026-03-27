import { useState } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import type { LogEntry } from '../types';

/**
 * Log-Ansicht
 *
 * BACKEND ERFORDERLICH:
 *   - GET /logs?limit=N
 *
 * Aktuell Mock-Daten. Struktur steht für echte Anbindung bereit.
 */

const MOCK_LOGS: LogEntry[] = [
  { timestamp: '2025-03-15T14:32:10Z', level: 'info', source: 'router', message: 'POST /route – qwen2.5-coder:1.5b – 1240ms' },
  { timestamp: '2025-03-15T14:30:05Z', level: 'info', source: 'health', message: 'GET /health – 200 OK' },
  { timestamp: '2025-03-15T14:28:00Z', level: 'warn', source: 'router', message: 'Ollama-Antwort langsam: 4200ms' },
  { timestamp: '2025-03-15T14:20:00Z', level: 'error', source: 'router', message: 'Ollama nicht erreichbar – Timeout nach 10000ms' },
  { timestamp: '2025-03-15T14:15:00Z', level: 'info', source: 'system', message: 'Router gestartet auf 0.0.0.0:8071' },
  { timestamp: '2025-03-15T14:14:58Z', level: 'info', source: 'system', message: 'Konfiguration geladen' },
];

const LEVEL_CLASS: Record<LogEntry['level'], string> = {
  info: 'log__level--info',
  warn: 'log__level--warn',
  error: 'log__level--error',
};

export function Logs() {
  const [filter, setFilter] = useState<'all' | LogEntry['level']>('all');
  const filtered = filter === 'all' ? MOCK_LOGS : MOCK_LOGS.filter((l) => l.level === filter);

  return (
    <Layout title="Logs & Ereignisse">
      <div className="alert alert--warn" style={{ marginBottom: '1.5rem' }}>
        <strong>Backend fehlt:</strong> Diese Ansicht zeigt Mock-Daten.
        Für echte Logs wird GET /logs benötigt.
      </div>

      <Card title="Letzte Ereignisse" tag="MOCK">
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
        </div>

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
      </Card>
    </Layout>
  );
}
