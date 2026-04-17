import { useEffect, useMemo, useState } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import {
  ApiRequestError,
  createModelRegistryEntry,
  createModelPullJob,
  deleteModelRegistryEntry,
  fetchModelRegistry,
  fetchModelPullJobs,
  fetchModels,
  fetchSettings,
  sendRoute,
  updateModelRegistryEntry,
  updateSettings,
} from '../api/client';
import { CONFIG } from '../config';
import type {
  ModelPullJob,
  ModelRegistryEntry,
  OllamaModel,
  RouteResponse,
  RouterSettings,
} from '../types';

interface RegistryDraft {
  name: string;
  description: string;
  enabled: boolean;
}

function isReadOnlyRole(role: ModelRegistryEntry['role']) {
  return role === 'default' || role === 'large';
}

export function Models() {
  const [testPrompt, setTestPrompt] = useState('Antworte kurz: Was ist 2+2?');
  const [testResult, setTestResult] = useState<RouteResponse | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  const [settings, setSettings] = useState<RouterSettings | null>(null);
  const [settingsError, setSettingsError] = useState<string | null>(null);

  const [models, setModels] = useState<OllamaModel[]>([]);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [modelsLoading, setModelsLoading] = useState(false);

  const [registry, setRegistry] = useState<ModelRegistryEntry[]>([]);
  const [registryError, setRegistryError] = useState<string | null>(null);
  const [registryLoading, setRegistryLoading] = useState(false);

  const [newModel, setNewModel] = useState<RegistryDraft>({
    name: '',
    description: '',
    enabled: true,
  });
  const [createError, setCreateError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [applyingModelName, setApplyingModelName] = useState<string | null>(null);
  const [pullModelName, setPullModelName] = useState('');
  const [pulling, setPulling] = useState(false);
  const [pullJobs, setPullJobs] = useState<ModelPullJob[]>([]);
  const [pullJobsError, setPullJobsError] = useState<string | null>(null);

  const installedNames = useMemo(() => new Set(models.map((model) => model.name)), [models]);

  async function loadSettings() {
    try {
      const current = await fetchSettings();
      setSettings(current);
      setSettingsError(null);
    } catch (err) {
      setSettings(null);
      setSettingsError(err instanceof ApiRequestError ? err.message : 'Router-Settings konnten nicht geladen werden.');
    }
  }

  async function loadModels() {
    setModelsLoading(true);
    setModelsError(null);
    try {
      const nextModels = await fetchModels();
      setModels(nextModels);
    } catch (err) {
      setModelsError(err instanceof ApiRequestError ? err.message : 'Modellliste konnte nicht geladen werden.');
    } finally {
      setModelsLoading(false);
    }
  }

  async function loadRegistry() {
    setRegistryLoading(true);
    setRegistryError(null);
    try {
      const entries = await fetchModelRegistry();
      setRegistry(entries);
    } catch (err) {
      setRegistryError(err instanceof ApiRequestError ? err.message : 'Modellregistrierung konnte nicht geladen werden.');
    } finally {
      setRegistryLoading(false);
    }
  }

  async function loadPullJobs() {
    try {
      const jobs = await fetchModelPullJobs(8);
      setPullJobs(jobs);
      setPullJobsError(null);
      if (jobs.some((job) => job.status === 'succeeded')) {
        void loadModels();
        void loadRegistry();
      }
    } catch (err) {
      setPullJobsError(err instanceof ApiRequestError ? err.message : 'Download-Jobs konnten nicht geladen werden.');
    }
  }

  async function refreshAll() {
    await Promise.all([loadSettings(), loadModels(), loadRegistry()]);
  }

  useEffect(() => {
    void refreshAll();
  }, []);

  useEffect(() => {
    void loadPullJobs();
  }, []);

  useEffect(() => {
    const hasActiveJob = pullJobs.some((job) => job.status === 'queued' || job.status === 'running');
    if (!hasActiveJob) return undefined;

    const timer = window.setInterval(() => {
      void loadPullJobs();
    }, 3000);

    return () => window.clearInterval(timer);
  }, [pullJobs]);

  async function handleTest() {
    const preferred = settings?.default_model ?? CONFIG.defaultModel;
    setTesting(true);
    setTestError(null);
    setTestResult(null);
    try {
      const res = await sendRoute({
        prompt: testPrompt,
        preferred_model: preferred,
        stream: false,
      });
      setTestResult(res);
    } catch (err) {
      setTestError(err instanceof ApiRequestError ? err.message : 'Fehler beim Testen');
    } finally {
      setTesting(false);
    }
  }

  async function handleCreateRegistryEntry() {
    setCreating(true);
    setCreateError(null);
    try {
      await createModelRegistryEntry({
        name: newModel.name,
        description: newModel.description,
        enabled: newModel.enabled,
      });
      setNewModel({ name: '', description: '', enabled: true });
      await loadRegistry();
    } catch (err) {
      setCreateError(err instanceof ApiRequestError ? err.message : 'Modell konnte nicht registriert werden.');
    } finally {
      setCreating(false);
    }
  }

  async function handleStartPull() {
    setPulling(true);
    setPullJobsError(null);
    try {
      await createModelPullJob(pullModelName);
      setPullModelName('');
      await loadPullJobs();
    } catch (err) {
      setPullJobsError(err instanceof ApiRequestError ? err.message : 'Modell-Download konnte nicht gestartet werden.');
    } finally {
      setPulling(false);
    }
  }

  async function handleSaveRegistryEntry(entry: ModelRegistryEntry) {
    setSavingId(entry.id);
    setRegistryError(null);
    try {
      await updateModelRegistryEntry(entry.id, {
        name: entry.name,
        description: entry.description,
        enabled: entry.enabled,
      });
      await loadRegistry();
    } catch (err) {
      setRegistryError(err instanceof ApiRequestError ? err.message : 'Modell konnte nicht gespeichert werden.');
    } finally {
      setSavingId(null);
    }
  }

  async function handleDeleteRegistryEntry(entry: ModelRegistryEntry) {
    setDeletingId(entry.id);
    setRegistryError(null);
    try {
      await deleteModelRegistryEntry(entry.id);
      await loadRegistry();
    } catch (err) {
      setRegistryError(err instanceof ApiRequestError ? err.message : 'Modell konnte nicht gelöscht werden.');
    } finally {
      setDeletingId(null);
    }
  }

  async function handleApplyAsDefault(modelName: string) {
    setApplyingModelName(modelName);
    setRegistryError(null);
    try {
      const next = await updateSettings({
        ...(settings ?? {}),
        default_model: modelName,
      });
      setSettings(next.settings);
      await loadRegistry();
    } catch (err) {
      setRegistryError(err instanceof ApiRequestError ? err.message : 'Fast Model konnte nicht gesetzt werden.');
    } finally {
      setApplyingModelName(null);
    }
  }

  async function handleApplyAsLarge(modelName: string) {
    setApplyingModelName(modelName);
    setRegistryError(null);
    try {
      const next = await updateSettings({
        ...(settings ?? {}),
        large_model: modelName,
      });
      setSettings(next.settings);
      await loadRegistry();
    } catch (err) {
      setRegistryError(err instanceof ApiRequestError ? err.message : 'Deep Model konnte nicht gesetzt werden.');
    } finally {
      setApplyingModelName(null);
    }
  }

  return (
    <Layout title="Modellverwaltung">
      <div className="grid grid--feature">
        <Card title="Router-Modelle" tag="LIVE">
          <div className="kv">
            <span className="kv__label">Fast Model</span>
            <code className="kv__value kv__value--highlight">{settings?.default_model ?? CONFIG.defaultModel}</code>
          </div>
          <div className="kv">
            <span className="kv__label">Deep Model</span>
            <code className="kv__value kv__value--highlight">{settings?.large_model ?? CONFIG.largeModel}</code>
          </div>
          <div className="kv">
            <span className="kv__label">Backend</span>
            <span className="kv__value">Ollama + persistente Registry</span>
          </div>
          <p className="text--muted text--sm" style={{ marginTop: '0.75rem' }}>
            Die Router-Modelle kommen jetzt aus GET /settings. Die Registry darunter dient als
            persistente Verwaltungsquelle für zusätzliche Modelle.
          </p>
          {settingsError && (
            <div className="alert alert--warn" style={{ marginTop: '1rem' }}>
              {settingsError}
            </div>
          )}
        </Card>

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
                <span className="kv__label">Request</span>
                <code className="kv__value">{testResult.request_id}</code>
              </div>
              <div className="kv">
                <span className="kv__label">Modell</span>
                <code className="kv__value">{testResult.model}</code>
              </div>
              <div className="kv">
                <span className="kv__label">Fertig</span>
                <span className="kv__value">{testResult.done ? 'Ja' : 'Nein'}</span>
              </div>
              <div style={{ marginTop: '0.75rem' }}>
                <label className="form-label">Antwort</label>
                <pre className="code-block" style={{ whiteSpace: 'pre-wrap' }}>{testResult.response}</pre>
              </div>
              <div className="kv">
                <span className="kv__label">Dauer</span>
                <span className="kv__value">{testResult.duration_ms} ms</span>
              </div>
              {testResult.done_reason && (
                <div className="kv">
                  <span className="kv__label">Done Reason</span>
                  <span className="kv__value">{testResult.done_reason}</span>
                </div>
              )}
              <div className="kv" style={{ marginTop: '0.75rem' }}>
                <span className="kv__label">Fairness</span>
                <span className="kv__value">
                  {testResult.fairness_risk ? `${testResult.fairness_risk}` : '–'}
                </span>
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

      <div className="grid grid--feature section">
        <Card title="Neue Registrierung" tag="LIVE">
          <div className="form-group">
            <label className="form-label">Modellname</label>
            <input
              className="form-input"
              value={newModel.name}
              onChange={(e) => setNewModel((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="z. B. qwen2.5-coder:14b"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Beschreibung</label>
            <textarea
              className="form-input form-input--textarea"
              rows={3}
              value={newModel.description}
              onChange={(e) => setNewModel((prev) => ({ ...prev, description: e.target.value }))}
              placeholder="Kurzbeschreibung des Modells"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Aktiv</label>
            <div className="toggle-row">
              <button
                className={`btn btn--sm ${newModel.enabled ? 'btn--active' : 'btn--ghost'}`}
                onClick={() => setNewModel((prev) => ({ ...prev, enabled: true }))}
              >
                Ja
              </button>
              <button
                className={`btn btn--sm ${!newModel.enabled ? 'btn--active' : 'btn--ghost'}`}
                onClick={() => setNewModel((prev) => ({ ...prev, enabled: false }))}
              >
                Nein
              </button>
            </div>
          </div>
          <button
            className="btn"
            onClick={handleCreateRegistryEntry}
            disabled={creating || !newModel.name.trim()}
          >
            {creating ? 'Registriere…' : 'Modell registrieren'}
          </button>
          {createError && (
            <div className="alert alert--error" style={{ marginTop: '1rem' }}>
              {createError}
            </div>
          )}
        </Card>

        <Card title="Installierte Modelle" tag="LIVE">
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Modell</th>
                  <th>Größe</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model) => (
                  <tr key={model.name}>
                    <td><code>{model.name}</code></td>
                    <td>{model.size}</td>
                    <td>
                      {installedNames.has(model.name) ? (
                        <span className="badge badge--ok"><span className="badge__dot" />Installiert</span>
                      ) : null}
                    </td>
                  </tr>
                ))}
                {models.length === 0 && !modelsLoading && (
                  <tr>
                    <td colSpan={3} className="text--muted" style={{ textAlign: 'center' }}>
                      Keine installierten Modelle gemeldet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          {modelsError && (
            <div className="alert alert--warn" style={{ marginTop: '1rem' }}>
              {modelsError}
            </div>
          )}
        </Card>
      </div>

      <div className="section">
        <Card title="Modell herunterladen" tag="LIVE">
          <p className="text--muted text--sm" style={{ marginBottom: '1rem' }}>
            Der Router stößt hier einen kontrollierten Pull-Job gegen die Ollama-API an.
            Der Status wird als Job protokolliert und regelmäßig aktualisiert.
          </p>
          <div className="grid grid--2">
            <div className="form-group">
              <label className="form-label">Modellname</label>
              <input
                className="form-input"
                value={pullModelName}
                onChange={(e) => setPullModelName(e.target.value)}
                placeholder="z. B. qwen2.5-coder:14b"
              />
            </div>
            <div className="form-group" style={{ alignSelf: 'end' }}>
              <button
                className="btn"
                onClick={() => void handleStartPull()}
                disabled={pulling || !pullModelName.trim()}
              >
                {pulling ? 'Starte…' : 'Pull starten'}
              </button>
            </div>
          </div>
          {pullJobsError && (
            <div className="alert alert--error" style={{ marginTop: '1rem' }}>
              {pullJobsError}
            </div>
          )}
          <div className="table-wrap">
            <table className="table" style={{ marginTop: '1rem' }}>
              <thead>
                <tr>
                  <th>Modell</th>
                  <th>Status</th>
                  <th>Fortschritt</th>
                  <th>Nachricht</th>
                </tr>
              </thead>
              <tbody>
                {pullJobs.map((job) => (
                  <tr key={job.id}>
                    <td><code>{job.model_name}</code></td>
                    <td>
                      <span className={`badge ${job.status === 'succeeded' ? 'badge--ok' : job.status === 'failed' ? 'badge--warn' : 'badge--info'}`}>
                        <span className="badge__dot" />
                        {job.status}
                      </span>
                    </td>
                    <td>{job.progress_percent !== null && job.progress_percent !== undefined ? `${job.progress_percent} %` : '–'}</td>
                    <td>{job.progress_message}</td>
                  </tr>
                ))}
                {pullJobs.length === 0 && (
                  <tr>
                    <td colSpan={4} className="text--muted" style={{ textAlign: 'center' }}>
                      Keine Pull-Jobs vorhanden.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <div className="section">
        <Card title="Persistente Modell-Registry" tag="LIVE">
          <p className="text--muted text--sm" style={{ marginBottom: '1rem' }}>
            Die Registry ist die Backend-Quelle für zusätzliche Modelle. Kernmodelle werden
            über die Router-Settings verwaltet und nur hier gespiegelt angezeigt.
          </p>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Modell</th>
                  <th>Rolle</th>
                  <th>Beschreibung</th>
                  <th>Installiert</th>
                  <th>Aktiv</th>
                  <th>Aktionen</th>
                </tr>
              </thead>
              <tbody>
                {registry.map((entry) => {
                  const installed = installedNames.has(entry.name);
                  const isReadOnly = isReadOnlyRole(entry.role);
                  return (
                    <tr key={entry.id}>
                      <td style={{ minWidth: '12rem' }}>
                        {isReadOnly ? (
                          <code>{entry.name}</code>
                        ) : (
                          <input
                            className="form-input"
                            value={entry.name}
                            onChange={(e) =>
                              setRegistry((prev) =>
                                prev.map((item) =>
                                  item.id === entry.id ? { ...item, name: e.target.value } : item,
                                ),
                              )
                            }
                          />
                        )}
                      </td>
                      <td>
                        <span className="badge badge--info">
                          <span className="badge__dot" />
                          {entry.role}
                        </span>
                      </td>
                      <td style={{ minWidth: '16rem' }}>
                        {isReadOnly ? (
                          entry.description
                        ) : (
                          <input
                            className="form-input"
                            value={entry.description}
                            onChange={(e) =>
                              setRegistry((prev) =>
                                prev.map((item) =>
                                  item.id === entry.id
                                    ? { ...item, description: e.target.value }
                                    : item,
                                ),
                              )
                            }
                          />
                        )}
                      </td>
                      <td>
                        {installed ? (
                          <span className="badge badge--ok"><span className="badge__dot" />Ja</span>
                        ) : (
                          <span className="badge badge--warn"><span className="badge__dot" />Nein</span>
                        )}
                      </td>
                      <td>
                        {isReadOnly ? (
                          <span className={`badge ${entry.enabled ? 'badge--ok' : 'badge--warn'}`}>
                            <span className="badge__dot" />
                            {entry.enabled ? 'Aktiv' : 'Inaktiv'}
                          </span>
                        ) : (
                          <div className="toggle-row">
                            <button
                              className={`btn btn--sm ${entry.enabled ? 'btn--active' : 'btn--ghost'}`}
                              onClick={() =>
                                setRegistry((prev) =>
                                  prev.map((item) =>
                                    item.id === entry.id ? { ...item, enabled: true } : item,
                                  ),
                                )
                              }
                            >
                              Ein
                            </button>
                            <button
                              className={`btn btn--sm ${!entry.enabled ? 'btn--active' : 'btn--ghost'}`}
                              onClick={() =>
                                setRegistry((prev) =>
                                  prev.map((item) =>
                                    item.id === entry.id ? { ...item, enabled: false } : item,
                                  ),
                                )
                              }
                            >
                              Aus
                            </button>
                          </div>
                        )}
                      </td>
                      <td>
                        <div className="toggle-row">
                          {!isReadOnly && (
                            <>
                              <button
                                className="btn btn--sm"
                                onClick={() => void handleSaveRegistryEntry(entry)}
                                disabled={savingId === entry.id}
                              >
                                {savingId === entry.id ? 'Speichere…' : 'Speichern'}
                              </button>
                              <button
                                className="btn btn--sm btn--ghost"
                                onClick={() => void handleDeleteRegistryEntry(entry)}
                                disabled={deletingId === entry.id}
                              >
                                {deletingId === entry.id ? 'Lösche…' : 'Löschen'}
                              </button>
                            </>
                          )}
                          <button
                            className="btn btn--sm"
                            onClick={() => void handleApplyAsDefault(entry.name)}
                            disabled={
                              applyingModelName === entry.name ||
                              !installed ||
                              settings?.large_model === entry.name
                            }
                          >
                            Als Fast Model
                          </button>
                          <button
                            className="btn btn--sm btn--ghost"
                            onClick={() => void handleApplyAsLarge(entry.name)}
                            disabled={
                              applyingModelName === entry.name ||
                              !installed ||
                              settings?.default_model === entry.name
                            }
                          >
                            Als Deep Model
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {registry.length === 0 && !registryLoading && (
                  <tr>
                    <td colSpan={6} className="text--muted" style={{ textAlign: 'center' }}>
                      Noch keine Registry-Einträge vorhanden.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          {registryError && (
            <div className="alert alert--warn" style={{ marginTop: '1rem' }}>
              {registryError}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
}
