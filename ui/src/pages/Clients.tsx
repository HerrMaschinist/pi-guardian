import { useState } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import type { ClientEntry } from '../types';

/**
 * Client-Verwaltung
 *
 * BACKEND ERFORDERLICH:
 *   - GET /clients
 *   - POST /clients
 *   - PUT /clients/:id
 *   - DELETE /clients/:id
 *
 * Die UI-Struktur steht vollständig.
 * Daten sind Mock bis die Backend-Endpunkte existieren.
 */

const MOCK_CLIENTS: ClientEntry[] = [
  {
    id: 'c1',
    name: 'PIBot Telegram',
    description: 'Telegram-Bot auf dem Pi',
    active: true,
    allowed_ip: '127.0.0.1',
    allowed_routes: ['/route', '/health'],
    api_key: '',
  },
  {
    id: 'c2',
    name: 'Werkstatt-Terminal',
    description: 'Interner Client im LAN',
    active: false,
    allowed_ip: '192.168.50.0/24',
    allowed_routes: ['/route'],
    api_key: '',
  },
];

export function Clients() {
  const [clients, setClients] = useState<ClientEntry[]>(MOCK_CLIENTS);
  const [editId, setEditId] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);

  // Formular-State für Neuanlage
  const emptyForm: Omit<ClientEntry, 'id'> = {
    name: '',
    description: '',
    active: true,
    allowed_ip: '',
    allowed_routes: ['/route'],
    api_key: '',
  };
  const [form, setForm] = useState(emptyForm);

  function handleToggle(id: string) {
    setClients((prev) =>
      prev.map((c) => (c.id === id ? { ...c, active: !c.active } : c))
    );
  }

  function handleDelete(id: string) {
    setClients((prev) => prev.filter((c) => c.id !== id));
  }

  function handleAdd() {
    if (!form.name.trim()) return;
    const newClient: ClientEntry = {
      ...form,
      id: `c${Date.now()}`,
    };
    setClients((prev) => [...prev, newClient]);
    setForm(emptyForm);
    setShowAdd(false);
  }

  return (
    <Layout title="Client-Verwaltung">
      <div className="alert alert--warn" style={{ marginBottom: '1.5rem' }}>
        <strong>Backend fehlt:</strong> Diese Seite arbeitet mit lokalen Mock-Daten.
        Für persistente Client-Verwaltung werden GET/POST/PUT/DELETE /clients benötigt.
      </div>

      <Card title="Registrierte Clients" tag="MOCK">
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
                    <button className="btn btn--sm btn--ghost" onClick={() => handleToggle(c.id)}>
                      {c.active ? 'Deaktivieren' : 'Aktivieren'}
                    </button>
                    <button className="btn btn--sm btn--danger" onClick={() => handleDelete(c.id)}>
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

        <button
          className="btn"
          onClick={() => setShowAdd(!showAdd)}
          style={{ marginTop: '1rem' }}
        >
          {showAdd ? 'Abbrechen' : 'Client hinzufügen'}
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
                placeholder="Wofür wird dieser Client genutzt?"
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
                    allowed_routes: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                  })
                }
                placeholder="/route, /health"
              />
            </div>
            <button className="btn" onClick={handleAdd}>
              Speichern (lokal)
            </button>
          </div>
        )}
      </Card>
    </Layout>
  );
}
