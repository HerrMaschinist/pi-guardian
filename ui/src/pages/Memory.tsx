import { useEffect, useState } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import {
  ApiRequestError,
  fetchActions,
  fetchAgents,
  fetchMemoryFeedback,
  fetchMemoryIncidents,
  fetchMemoryKnowledge,
  fetchMemoryRuns,
  fetchSkills,
} from '../api/client';
import type {
  ActionDefinition,
  AgentDefinition,
  MemoryFeedbackEntryRead,
  MemoryIncidentRead,
  MemoryKnowledgeEntryRead,
  MemoryRunSummary,
  SkillDefinition,
} from '../types';

interface MemoryNote {
  id: string;
  title: string;
  content: string;
  created_at: string;
}

const MEMORY_STORAGE_KEY = 'pi-guardian.memory.notes';

function readNotes(): MemoryNote[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(MEMORY_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as MemoryNote[]) : [];
  } catch {
    return [];
  }
}

function writeNotes(notes: MemoryNote[]) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(MEMORY_STORAGE_KEY, JSON.stringify(notes));
}

function formatDateTime(value?: string | null): string {
  if (!value) return '–';
  try {
    return new Date(value).toLocaleString('de-DE');
  } catch {
    return value;
  }
}

export function Memory() {
  const [agents, setAgents] = useState<AgentDefinition[]>([]);
  const [skills, setSkills] = useState<SkillDefinition[]>([]);
  const [actions, setActions] = useState<ActionDefinition[]>([]);
  const [runs, setRuns] = useState<MemoryRunSummary[]>([]);
  const [incidents, setIncidents] = useState<MemoryIncidentRead[]>([]);
  const [knowledge, setKnowledge] = useState<MemoryKnowledgeEntryRead[]>([]);
  const [feedback, setFeedback] = useState<MemoryFeedbackEntryRead[]>([]);
  const [notes, setNotes] = useState<MemoryNote[]>(() => readNotes());
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshedAt, setRefreshedAt] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);

    const results = await Promise.allSettled([
      fetchAgents(),
      fetchSkills(),
      fetchActions(),
      fetchMemoryRuns(),
      fetchMemoryIncidents(),
      fetchMemoryKnowledge(),
      fetchMemoryFeedback(),
    ]);

    const [agentsRes, skillsRes, actionsRes, runsRes, incidentsRes, knowledgeRes, feedbackRes] = results;

    if (agentsRes.status === 'fulfilled') setAgents(agentsRes.value);
    if (skillsRes.status === 'fulfilled') setSkills(skillsRes.value);
    if (actionsRes.status === 'fulfilled') setActions(actionsRes.value);
    if (runsRes.status === 'fulfilled') setRuns(runsRes.value);
    if (incidentsRes.status === 'fulfilled') setIncidents(incidentsRes.value);
    if (knowledgeRes.status === 'fulfilled') setKnowledge(knowledgeRes.value);
    if (feedbackRes.status === 'fulfilled') setFeedback(feedbackRes.value);

    const rejected = results.find((item) => item.status === 'rejected');
    if (rejected && rejected.status === 'rejected') {
      const reason = rejected.reason;
      setError(reason instanceof ApiRequestError ? reason.message : 'Memory-Daten konnten nicht vollständig geladen werden.');
    }

    setRefreshedAt(new Date().toLocaleTimeString('de-DE'));
    setLoading(false);
  }

  useEffect(() => {
    void load();
  }, []);

  function addNote() {
    if (!title.trim() || !content.trim()) return;
    const nextNotes = [
      {
        id: `note-${Date.now()}`,
        title: title.trim(),
        content: content.trim(),
        created_at: new Date().toISOString(),
      },
      ...notes,
    ];
    setNotes(nextNotes);
    writeNotes(nextNotes);
    setTitle('');
    setContent('');
  }

  function removeNote(id: string) {
    const nextNotes = notes.filter((note) => note.id !== id);
    setNotes(nextNotes);
    writeNotes(nextNotes);
  }

  return (
    <Layout title="Memory">
      <div className="grid grid--dense">
        <Card title="Memory Snapshot" tag="LIVE">
          <div className="kv">
            <span className="kv__label">Runs</span>
            <span className="kv__value">{runs.length}</span>
          </div>
          <div className="kv">
            <span className="kv__label">Incidents</span>
            <span className="kv__value">{incidents.length}</span>
          </div>
          <div className="kv">
            <span className="kv__label">Knowledge</span>
            <span className="kv__value">{knowledge.length}</span>
          </div>
          <div className="kv">
            <span className="kv__label">Feedback</span>
            <span className="kv__value">{feedback.length}</span>
          </div>
          <div className="kv">
            <span className="kv__label">Letztes Update</span>
            <span className="kv__value">{refreshedAt ?? '–'}</span>
          </div>
          <button className="btn btn--sm" onClick={() => void load()} disabled={loading}>
            {loading ? 'Lade…' : 'Neu laden'}
          </button>
        </Card>

        <Card title="Registry-Snapshot" tag="LIVE">
          <div className="kv">
            <span className="kv__label">Agenten</span>
            <span className="kv__value">{agents.length}</span>
          </div>
          <div className="kv">
            <span className="kv__label">Skills</span>
            <span className="kv__value">{skills.length}</span>
          </div>
          <div className="kv">
            <span className="kv__label">Actions</span>
            <span className="kv__value">{actions.length}</span>
          </div>
          <p className="text--sm" style={{ marginTop: '0.75rem' }}>
            Die Registry kommt aus dem Router-Backend. Sie ist unabhängig von den
            Memory-Runs und zeigt den aktuellen Freigabestand.
          </p>
        </Card>

        <Card title="Browser-Notizen" tag="LOCAL">
          <div className="kv">
            <span className="kv__label">Notizen</span>
            <span className="kv__value">{notes.length}</span>
          </div>
          <p className="text--muted text--sm" style={{ marginTop: '0.75rem' }}>
            Diese Notizen bleiben lokal im Browser erhalten und helfen beim operativen Arbeiten.
          </p>
        </Card>
      </div>

      {error && (
        <div className="alert alert--warn" style={{ marginTop: '1.5rem' }}>
          <strong>Teilfehler:</strong> {error}
        </div>
      )}

      <div className="grid grid--2 section">
        <Card title="Aktuelle Runs" tag="API">
          <div className="table-wrap">
            <table className="table">
            <thead>
              <tr>
                <th>Zeit</th>
                <th>Agent</th>
                <th>Modell</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.run_id}>
                  <td>
                    <strong>{formatDateTime(run.started_at)}</strong>
                    <div className="text--muted text--sm">{run.run_id}</div>
                  </td>
                  <td>{run.agent_name}</td>
                  <td>{run.used_model ?? '–'}</td>
                  <td>{run.success ? 'Erfolgreich' : 'Fehlgeschlagen'}</td>
                </tr>
              ))}
              {runs.length === 0 && !loading && (
                <tr>
                  <td colSpan={4} className="text--muted" style={{ textAlign: 'center' }}>
                    Keine Memory-Runs vorhanden.
                  </td>
                </tr>
              )}
            </tbody>
            </table>
          </div>
        </Card>

        <Card title="Incidents" tag="API">
          <div className="table-wrap">
            <table className="table">
            <thead>
              <tr>
                <th>Titel</th>
                <th>Schwere</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((incident) => (
                <tr key={incident.id}>
                  <td>
                    <strong>{incident.title}</strong>
                    <div className="text--muted text--sm">{incident.summary}</div>
                  </td>
                  <td>{incident.severity}</td>
                  <td>{incident.status}</td>
                </tr>
              ))}
              {incidents.length === 0 && !loading && (
                <tr>
                  <td colSpan={3} className="text--muted" style={{ textAlign: 'center' }}>
                    Keine Incidents gespeichert.
                  </td>
                </tr>
              )}
            </tbody>
            </table>
          </div>
        </Card>
      </div>

      <div className="grid grid--2 section">
        <Card title="Knowledge" tag="API">
          <div className="table-wrap">
            <table className="table">
            <thead>
              <tr>
                <th>Titel</th>
                <th>Vertrauen</th>
                <th>Bestätigt</th>
              </tr>
            </thead>
            <tbody>
              {knowledge.map((entry) => (
                <tr key={entry.id}>
                  <td>
                    <strong>{entry.title}</strong>
                    <div className="text--muted text--sm">{entry.probable_cause}</div>
                  </td>
                  <td>{entry.confidence}</td>
                  <td>{entry.confirmed ? 'Ja' : 'Nein'}</td>
                </tr>
              ))}
              {knowledge.length === 0 && !loading && (
                <tr>
                  <td colSpan={3} className="text--muted" style={{ textAlign: 'center' }}>
                    Keine Knowledge-Einträge gespeichert.
                  </td>
                </tr>
              )}
            </tbody>
            </table>
          </div>
        </Card>

        <Card title="Feedback" tag="API">
          <div className="table-wrap">
            <table className="table">
            <thead>
              <tr>
                <th>Verlauf</th>
                <th>Entscheidung</th>
                <th>Autor</th>
              </tr>
            </thead>
            <tbody>
              {feedback.map((entry) => (
                <tr key={entry.id}>
                  <td>
                    <strong>{entry.comment}</strong>
                    <div className="text--muted text--sm">{entry.related_run_id ?? '–'}</div>
                  </td>
                  <td>{entry.verdict}</td>
                  <td>{entry.created_by}</td>
                </tr>
              ))}
              {feedback.length === 0 && !loading && (
                <tr>
                  <td colSpan={3} className="text--muted" style={{ textAlign: 'center' }}>
                    Kein Feedback gespeichert.
                  </td>
                </tr>
              )}
            </tbody>
            </table>
          </div>
        </Card>
      </div>

      <div className="grid grid--2 section">
        <Card title="Persistierte Notizen" tag="LOCAL">
          <div className="form-group">
            <label className="form-label">Titel</label>
            <input
              className="form-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Beobachtung oder Erkenntnis"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Inhalt</label>
            <textarea
              className="form-input form-input--textarea"
              rows={4}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Kurze operative Notiz"
            />
          </div>
          <button className="btn" onClick={addNote}>
            Notiz speichern
          </button>

          <div style={{ marginTop: '1rem' }}>
            {notes.length === 0 ? (
              <p className="text--muted">Noch keine lokalen Notizen gespeichert.</p>
            ) : (
              <div className="gap-list">
                {notes.map((note) => (
                  <div key={note.id} className="result-box">
                    <div className="kv">
                      <span className="kv__label">{note.title}</span>
                      <span className="kv__value text--muted">
                        {new Date(note.created_at).toLocaleString('de-DE')}
                      </span>
                    </div>
                    <p style={{ margin: '0.75rem 0' }}>{note.content}</p>
                    <button className="btn btn--sm btn--ghost" onClick={() => removeNote(note.id)}>
                      Löschen
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        <Card title="Registry-Details" tag="API">
          <div className="table-wrap">
            <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Read only</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.name}>
                  <td>
                    <strong>{agent.name}</strong>
                    <div className="text--muted text--sm">{agent.description}</div>
                  </td>
                  <td>{agent.read_only ? 'Ja' : 'Nein'}</td>
                  <td>{agent.enabled === false ? 'Inaktiv' : 'Aktiv'}</td>
                </tr>
              ))}
            </tbody>
            </table>
          </div>
        </Card>
      </div>
    </Layout>
  );
}
