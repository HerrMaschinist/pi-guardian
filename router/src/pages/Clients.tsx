import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import { useApiCall } from '../hooks/useApi';
import {
  fetchClients,
  fetchIntegrationGuide,
  createClient,
  updateClient,
  deleteClient,
  ApiRequestError,
} from '../api/client';
import type { ClientEntry, IntegrationGuide } from '../types';

type FormData = {
  name: string;
  description: string;
  active: boolean;
  allowed_ip: string;
  allowed_routes: string[];
};

const DEFAULT_ALLOWED_ROUTES = ['/route', '/health', '/api/tags', '/api/generate', '/api/chat'];

const EMPTY_FORM: FormData = {
  name: '',
  description: '',
  active: true,
  allowed_ip: '192.168.50.0/24',
  allowed_routes: [...DEFAULT_ALLOWED_ROUTES],
};

function clientToForm(client: ClientEntry): FormData {
  return {
    name: client.name,
    description: client.description,
    active: client.active,
    allowed_ip: client.allowed_ip,
    allowed_routes:
      client.allowed_routes.length > 0 ? [...client.allowed_routes] : [...DEFAULT_ALLOWED_ROUTES],
  };
}

export function Clients() {
  const [clients, setClients] = useState<ClientEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingClientId, setEditingClientId] = useState<number | null>(null);
  const [form, setForm] = useState<FormData>({ ...EMPTY_FORM });
  const [submitting, setSubmitting] = useState(false);
  const [actionId, setActionId] = useState<number | null>(null);
  const [newApiKey, setNewApiKey] = useState<string | null>(null);
  const {
    data: integrationGuide,
    loading: integrationLoading,
    error: integrationError,
    execute: loadIntegrationGuide,
  } = useApiCall<IntegrationGuide>();

  const isEditing = editingClientId !== null;

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

  useEffect(() => {
    loadIntegrationGuide(fetchIntegrationGuide).catch(() => {});
  }, [loadIntegrationGuide]);

  function openCreateForm() {
    setEditingClientId(null);
    setForm({ ...EMPTY_FORM });
    setShowForm(true);
    setNewApiKey(null);
    setError(null);
  }

  function openEditForm(client: ClientEntry) {
    setEditingClientId(client.id);
    setForm(clientToForm(client));
    setShowForm(true);
    setNewApiKey(null);
    setError(null);
  }

  function closeForm() {
    setShowForm(false);
    setEditingClientId(null);
    setForm({ ...EMPTY_FORM });
  }

  async function handleSubmit() {
    if (!form.name.trim()) return;
    setSubmitting(true);
    setError(null);

    try {
      const payload = {
        name: form.name,
        description: form.description,
        active: form.active,
        allowed_ip: form.allowed_ip,
        allowed_routes: form.allowed_routes,
      };

      if (isEditing && editingClientId !== null) {
        const updated = await updateClient(editingClientId, payload);
        setClients((prev) => prev.map((client) => (client.id === updated.id ? updated : client)));
      } else {
        const created = await createClient(payload);
        setClients((prev) => [created, ...prev]);
        if (created.api_key) {
          setNewApiKey(created.api_key);
        }
      }

      closeForm();
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.message
          : isEditing
            ? 'Fehler beim Aktualisieren'
            : 'Fehler beim Erstellen'
      );
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
            type="button"
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
                        onClick={() => openEditForm(c)}
                        disabled={actionId === c.id}
                        type="button"
                      >
                        Bearbeiten
                      </button>
                      <button
                        className="btn btn--sm btn--ghost"
                        onClick={() => handleToggle(c)}
                        disabled={actionId === c.id}
                        type="button"
                      >
                        {actionId === c.id ? '...' : c.active ? 'Deaktivieren' : 'Aktivieren'}
                      </button>
                      <button
                        className="btn btn--sm btn--danger"
                        onClick={() => handleDelete(c)}
                        disabled={actionId === c.id}
                        type="button"
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

        <div className="btn-group" style={{ marginTop: '1rem' }}>
          <button
            className="btn"
            onClick={showForm ? closeForm : openCreateForm}
            disabled={loading}
            type="button"
          >
            {showForm ? 'Abbrechen' : 'Client hinzufuegen'}
          </button>
        </div>

        {showForm && (
          <div className="form-section" style={{ marginTop: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Status</label>
              <div className="toggle-row">
                <button
                  className={`btn btn--sm ${form.active ? 'btn--active' : 'btn--ghost'}`}
                  onClick={() => setForm({ ...form, active: true })}
                  type="button"
                >
                  Aktiv
                </button>
                <button
                  className={`btn btn--sm ${!form.active ? 'btn--active' : 'btn--ghost'}`}
                  onClick={() => setForm({ ...form, active: false })}
                  type="button"
                >
                  Inaktiv
                </button>
              </div>
            </div>

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

            <div className="btn-group">
              <button
                className="btn"
                onClick={handleSubmit}
                disabled={submitting || !form.name.trim()}
                type="button"
              >
                {submitting
                  ? 'Speichert...'
                  : isEditing
                    ? 'Client speichern'
                    : 'Client anlegen'}
              </button>
              <button
                className="btn btn--ghost"
                onClick={closeForm}
                disabled={submitting}
                type="button"
              >
                {isEditing ? 'Bearbeitung abbrechen' : 'Formular schliessen'}
              </button>
            </div>
          </div>
        )}
      </Card>

      <div style={{ marginTop: '1.5rem' }}>
        <Card title="Schnellintegration" tag="SECURE">
          {integrationLoading ? (
            <span className="text--muted">Lädt…</span>
          ) : integrationError ? (
            <div className="alert alert--warn">
              Integrationshilfe konnte nicht geladen werden: {integrationError}
            </div>
          ) : integrationGuide ? (
            <div className="grid grid--2">
              <div className="form-group">
                <label className="form-label">Router-URL</label>
                <code style={{ display: 'block', whiteSpace: 'break-spaces' }}>
                  {integrationGuide.router_base_url}
                </code>
              </div>
              <div className="form-group">
                <label className="form-label">{integrationGuide.auth_header_name}</label>
                <code style={{ display: 'block', whiteSpace: 'break-spaces' }}>
                  {integrationGuide.auth_header_example}
                </code>
              </div>

              <div className="form-group">
                <label className="form-label">Erlaubte Routen</label>
                <code style={{ display: 'block', whiteSpace: 'break-spaces' }}>
                  {integrationGuide.allowed_routes.join(', ')}
                </code>
              </div>
              <div className="form-group">
                <label className="form-label">Sicherheitskontrollen</label>
                <ul className="text--muted" style={{ margin: 0, paddingLeft: '1.2rem' }}>
                  {integrationGuide.security_controls.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label className="form-label">Client-Beispiel</label>
                <pre
                  style={{
                    margin: 0,
                    padding: '0.9rem',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(255,255,255,0.04)',
                    overflowX: 'auto',
                  }}
                >
{JSON.stringify(integrationGuide.example_create_client, null, 2)}
                </pre>
              </div>

              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label className="form-label">cURL</label>
                <pre
                  style={{
                    margin: 0,
                    padding: '0.9rem',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(255,255,255,0.04)',
                    overflowX: 'auto',
                  }}
                >
{integrationGuide.example_curl}
                </pre>
              </div>
            </div>
          ) : (
            <span className="text--muted">Keine Integrationshilfe verfügbar.</span>
          )}
        </Card>
      </div>
    </Layout>
  );
}
