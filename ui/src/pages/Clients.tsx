import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import {
  fetchClients,
  createClient,
  updateClient,
  deleteClient,
  ApiRequestError,
} from '../api/client';
import type { ClientEntry } from '../types';

type FormData = {
  name: string;
  description: string;
  active: boolean;
  allowed_ip: string;
  allowed_routes: string[];
};

const EMPTY_FORM: FormData = {
  name: '',
  description: '',
  active: true,
  allowed_ip: '192.168.50.0/24',
  allowed_routes: ['/route', '/health'],
};

export function Clients() {
  const [clients, setClients] = useState<ClientEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState<FormData>({ ...EMPTY_FORM });
  const [submitting, setSubmitting] = useState(false);
  const [actionId, setActionId] = useState<number | null>(null);
  // API-Key einmalig nach Erstellung anzeigen
  const [newApiKey, setNewApiKey] = useState<string | null>(null);

  const loadClients = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchClients();
      setClients(data);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : 'Fehler beim Laden der Clients');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadClients();
  }, [loadClients]);

  async function handleAdd() {
    if (!form.name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const created = await createClient({
        name: form.name,
        description: form.description,
        active: form.active,
        allowed_ip: form.allowed_ip,
        allowed_routes: form.allowed_routes,
      });
      setClients((prev) => [created, ...prev]);
      if (created.api_key) {
        setNewApiKey(created.api_key);
      }
      setForm({ ...EMPTY_FORM });
      setShowAdd(false);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : 'Fehler beim Erstellen');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleToggle(c: ClientEntry) {
    setActionId(c.id);
    setError(null);
    try {
      const updated = await updateClient(c.id, { active: !c.active });
      setClients((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : 'Fehler beim Aktualisieren');
    } finally {
      setActionId(null);
    }
  }

  async function handleDelete(c: ClientEntry) {
    if (!confirm(`Client "${c.name}" wirklich loeschen?`)) return;
    setActionId(c.id);
    setError(null);
    try {
      await deleteClient(c.id);
      setClients((prev) => prev.filter((x) => x.id !== c.id));
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : 'Fehler beim Loeschen');
    } finally {
      setActionId(null);
    }
  }

  return (
    <Layout title="Client-Verwaltung">
      {/* API-Key-Anzeige nach Erstellung */}
      {newApiKey && (
        <div className="alert alert--ok" style={{ marginBottom: '1.5rem' }}>
          <strong>Neuer API-Key (wird nicht erneut angezeigt):</strong>
          <br />
          <code style={{ userSelect: 'all', fontSize: '0.9rem' }}>{newApiKey}</code>
          <br />
          <button
            className="btn btn--sm btn--ghost"
            style={{ marginTop: '0.5rem' }}
            onClick={() => setNewApiKey(null)}
          >
            Verstanden
          </button>
        </div>
      )}

      {error && (
        <div className="alert alert--error" style={{ marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      <Card title="Registrierte Clients" tag="LIVE">
        {loading ? (
          <span className="text--muted">Laedt...</span>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Beschreibung</th>
                <th>IP / Host</th>
                <th>Routen</th>
                <th>Status</th>
                <th>Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((c) => (
                <tr key={c.id}>
                  <td><strong>{c.name}</strong></td>
                  <td className="text--muted">{c.description}</td>
                  <td><code>{c.allowed_ip}</code></td>
                  <td><code>{c.allowed_routes.join(', ')}</code></td>
                  <td>
                    {c.active ? (
                      <span className="badge badge--ok"><span className="badge__dot" />Aktiv</span>
                    ) : (
                      <span className="badge badge--fail"><span className="badge__dot" />Inaktiv</span>
                    )}
                  </td>
                  <td>
                    <div className="btn-group">
                      <button
                        className="btn btn--sm btn--ghost"
                        onClick={() => handleToggle(c)}
                        disabled={actionId === c.id}
                      >
                        {actionId === c.id ? '...' : c.active ? 'Deaktivieren' : 'Aktivieren'}
                      </button>
                      <button
                        className="btn btn--sm btn--danger"
                        onClick={() => handleDelete(c)}
                        disabled={actionId === c.id}
                      >
                        Entfernen
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {clients.length === 0 && (
                <tr>
                  <td colSpan={6} className="text--muted" style={{ textAlign: 'center' }}>
                    Keine Clients registriert.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        <button
          className="btn"
          onClick={() => setShowAdd(!showAdd)}
          style={{ marginTop: '1rem' }}
          disabled={loading}
        >
          {showAdd ? 'Abbrechen' : 'Client hinzufuegen'}
        </button>

        {showAdd && (
          <div className="form-section" style={{ marginTop: '1rem' }}>
            <div className="grid grid--2">
              <div className="form-group">
                <label className="form-label">Name</label>
                <input
                  className="form-input"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="z.B. Werkstatt-Client"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Erlaubte IP / Subnetz</label>
                <input
                  className="form-input"
                  value={form.allowed_ip}
                  onChange={(e) => setForm({ ...form, allowed_ip: e.target.value })}
                  placeholder="z.B. 192.168.50.0/24"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Beschreibung</label>
              <input
                className="form-input"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Wofuer wird dieser Client genutzt?"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Erlaubte Routen (kommasepariert)</label>
              <input
                className="form-input"
                value={form.allowed_routes.join(', ')}
                onChange={(e) =>
                  setForm({
                    ...form,
                    allowed_routes: e.target.value
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean),
                  })
                }
                placeholder="/route, /health"
              />
            </div>
            <button
              className="btn"
              onClick={handleAdd}
              disabled={submitting || !form.name.trim()}
            >
              {submitting ? 'Speichert...' : 'Client anlegen'}
            </button>
          </div>
        )}
      </Card>
    </Layout>
  );
}
