import { useEffect, useMemo, useState } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import { ApiRequestError, fetchActions, fetchAgents, fetchSkills } from '../api/client';
import type { ActionDefinition, AgentDefinition, SkillDefinition } from '../types';

function formatList(value?: string[]) {
  if (!value || value.length === 0) return '–';
  return value.join(', ');
}

function formatDateTime(value?: string | null) {
  if (!value) return '–';
  try {
    return new Date(value).toLocaleString('de-DE');
  } catch {
    return value;
  }
}

export function Agents() {
  const [agents, setAgents] = useState<AgentDefinition[]>([]);
  const [skills, setSkills] = useState<SkillDefinition[]>([]);
  const [actions, setActions] = useState<ActionDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshedAt, setRefreshedAt] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [nextAgents, nextSkills, nextActions] = await Promise.all([
        fetchAgents(),
        fetchSkills(),
        fetchActions(),
      ]);
      setAgents(nextAgents);
      setSkills(nextSkills);
      setActions(nextActions);
      setRefreshedAt(new Date().toLocaleTimeString('de-DE'));
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : 'Agentendaten konnten nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return undefined;
    const timer = window.setInterval(() => {
      void load();
    }, 15000);
    return () => window.clearInterval(timer);
  }, [autoRefresh]);

  const supervisor = agents.find((agent) => agent.name === 'guardian_supervisor') ?? agents[0] ?? null;
  const agentsWithActivity = useMemo(
    () => agents.filter((agent) => agent.activity?.last_run_at),
    [agents],
  );
  const lastActiveAgent = useMemo(() => {
    return [...agentsWithActivity].sort((left, right) => {
      const leftTime = left.activity?.last_run_at ? new Date(left.activity.last_run_at).getTime() : 0;
      const rightTime = right.activity?.last_run_at ? new Date(right.activity.last_run_at).getTime() : 0;
      return rightTime - leftTime;
    })[0] ?? null;
  }, [agentsWithActivity]);

  return (
    <Layout title="Agenten">
      <div className="grid grid--dense">
        <Card title="Registry" tag="LIVE">
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
          <div className="kv">
            <span className="kv__label">Mit Aktivität</span>
            <span className="kv__value">{agentsWithActivity.length}</span>
          </div>
          <div className="kv">
            <span className="kv__label">Letztes Update</span>
            <span className="kv__value">{refreshedAt ?? '–'}</span>
          </div>
          <button className="btn btn--sm" onClick={() => void load()} disabled={loading}>
            {loading ? 'Lade…' : 'Neu laden'}
          </button>
        </Card>

        <Card title="guardian_supervisor" tag={supervisor?.read_only ? 'READ ONLY' : 'CUSTOM'}>
          {supervisor ? (
            <>
              <div className="kv">
                <span className="kv__label">Typ</span>
                <span className="kv__value">{supervisor.agent_type ?? '–'}</span>
              </div>
              <div className="kv">
                <span className="kv__label">Aktiv</span>
                <span className="kv__value">{supervisor.settings?.active === false ? 'Nein' : 'Ja'}</span>
              </div>
              <div className="kv">
                <span className="kv__label">Modell</span>
                <code className="kv__value">{supervisor.settings?.preferred_model ?? '–'}</code>
              </div>
              <div className="kv">
                <span className="kv__label">Max Steps</span>
                <span className="kv__value">{supervisor.settings?.max_steps ?? supervisor.max_steps ?? '–'}</span>
              </div>
              <div className="kv">
                <span className="kv__label">Letzter Lauf</span>
                <span className="kv__value">{formatDateTime(supervisor.activity?.last_run_at)}</span>
              </div>
              <div className="kv">
                <span className="kv__label">Letzter Status</span>
                <span className="kv__value">
                  {supervisor.activity?.last_status === 'success'
                    ? 'Erfolgreich'
                    : supervisor.activity?.last_status === 'failed'
                      ? 'Fehlgeschlagen'
                      : '–'}
                </span>
              </div>
              <div className="kv">
                <span className="kv__label">Tools</span>
                <span className="kv__value">{formatList(supervisor.allowed_tools)}</span>
              </div>
            </>
          ) : (
            <p className="text--muted">Kein Agent gefunden.</p>
          )}
        </Card>

        <Card title="Zugriff" tag="STATUS">
          <p className="text--sm">
            Die Oberfläche nutzt den im Browser gespeicherten Router API-Key. Ohne gültigen
            Schlüssel bleiben geschützte Agentenrouten im Fehlerzustand.
          </p>
          <div className="kv" style={{ marginTop: '0.75rem' }}>
            <span className="kv__label">Auto-Refresh</span>
            <div className="toggle-row">
              <button
                className={`btn btn--sm ${autoRefresh ? 'btn--active' : 'btn--ghost'}`}
                onClick={() => setAutoRefresh(true)}
                type="button"
              >
                Aktiv
              </button>
              <button
                className={`btn btn--sm ${!autoRefresh ? 'btn--active' : 'btn--ghost'}`}
                onClick={() => setAutoRefresh(false)}
                type="button"
              >
                Aus
              </button>
            </div>
          </div>
          <div className="kv">
            <span className="kv__label">Zuletzt aktiv</span>
            <span className="kv__value">{lastActiveAgent?.name ?? '–'}</span>
          </div>
          <p className="text--muted text--sm">
            Konfiguriere den Schlüssel in <strong>Einstellungen</strong>.
          </p>
        </Card>
      </div>

      {error && (
        <div className="alert alert--error" style={{ marginTop: '1.5rem' }}>
          <strong>Fehler:</strong> {error}
        </div>
      )}

      <div className="grid grid--feature section">
        <Card title="Agentenliste" tag="API">
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Typ</th>
                  <th>Status</th>
                  <th>Letzter Lauf</th>
                  <th>Modell</th>
                  <th>Letzte Aufgabe</th>
                </tr>
              </thead>
              <tbody>
                {agents.map((agent) => (
                  <tr key={agent.name}>
                    <td>
                      <strong>{agent.name}</strong>
                    </td>
                    <td>{agent.agent_type ?? '–'}</td>
                    <td>{agent.enabled === false ? 'Inaktiv' : 'Aktiv'}</td>
                    <td>
                      <strong>{formatDateTime(agent.activity?.last_run_at)}</strong>
                      <div className="text--muted text--sm">
                        {agent.activity?.last_status === 'success'
                          ? 'Erfolgreich'
                          : agent.activity?.last_status === 'failed'
                            ? 'Fehlgeschlagen'
                            : 'Keine Runs'}
                      </div>
                    </td>
                    <td>{agent.activity?.last_model ?? agent.settings?.preferred_model ?? '–'}</td>
                    <td>{agent.activity?.last_activity ?? '–'}</td>
                  </tr>
                ))}
                {agents.length === 0 && !loading && (
                  <tr>
                    <td colSpan={6} className="text--muted" style={{ textAlign: 'center' }}>
                      Keine Agenten geladen.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Agentendetails" tag="DETAILS">
          {supervisor ? (
            <div className="result-box">
              <div className="kv">
                <span className="kv__label">Beschreibung</span>
                <span className="kv__value">{supervisor.description}</span>
              </div>
              <div className="kv">
                <span className="kv__label">Letzter Run</span>
                <span className="kv__value">{supervisor.activity?.last_run_id ?? '–'}</span>
              </div>
              <div className="kv">
                <span className="kv__label">Letzte Aktivität</span>
                <span className="kv__value">{supervisor.activity?.last_activity ?? '–'}</span>
              </div>
              <div className="kv">
                <span className="kv__label">Letzte Antwort</span>
                <span className="kv__value">{supervisor.activity?.last_result_preview ?? '–'}</span>
              </div>
              <div className="kv" style={{ marginTop: '0.5rem' }}>
                <span className="kv__label">Systemprompt</span>
                <pre className="code-block" style={{ whiteSpace: 'pre-wrap' }}>
                  {supervisor.system_prompt ?? '–'}
                </pre>
              </div>
              <div className="kv" style={{ marginTop: '0.5rem' }}>
                <span className="kv__label">Verhalten</span>
                <span className="kv__value">
                  {supervisor.settings?.behavior
                    ? `${supervisor.settings.behavior.analysis_mode} / ${supervisor.settings.behavior.response_depth} / ${supervisor.settings.behavior.risk_sensitivity}`
                    : '–'}
                </span>
              </div>
              <div className="kv" style={{ marginTop: '0.5rem' }}>
                <span className="kv__label">Policy</span>
                <span className="kv__value">
                  {supervisor.settings?.policy
                    ? `${supervisor.settings.policy.read_only ? 'read only' : 'writable'} · ${supervisor.settings.policy.allowed_tools.length} tools · max ${supervisor.settings.policy.max_steps} steps`
                    : '–'}
                </span>
              </div>
              <div className="kv" style={{ marginTop: '0.5rem' }}>
                <span className="kv__label">Persönlichkeit</span>
                <span className="kv__value">
                  {supervisor.settings?.personality
                    ? `${supervisor.settings.personality.style} · ${supervisor.settings.personality.tone} · ${supervisor.settings.personality.verbosity}`
                    : '–'}
                </span>
              </div>
              <div className="kv" style={{ marginTop: '0.5rem' }}>
                <span className="kv__label">Custom Instruction</span>
                <span className="kv__value">{supervisor.settings?.custom_instruction ?? '–'}</span>
              </div>
            </div>
          ) : (
            <p className="text--muted">Keine Detaildaten verfügbar.</p>
          )}
        </Card>
      </div>

      <div className="grid grid--2 section">
        <Card title="Skills" tag="API">
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Version</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {skills.map((skill) => (
                  <tr key={skill.name}>
                    <td>
                      <strong>{skill.name}</strong>
                      <div className="text--muted text--sm">{skill.description}</div>
                    </td>
                    <td>{skill.version ?? '–'}</td>
                    <td>{skill.enabled === false ? 'Inaktiv' : 'Aktiv'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Actions" tag="API">
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Approval</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {actions.map((action) => (
                  <tr key={action.name}>
                    <td>
                      <strong>{action.name}</strong>
                      <div className="text--muted text--sm">{action.description}</div>
                    </td>
                    <td>{action.requires_approval ? 'Ja' : 'Nein'}</td>
                    <td>{action.enabled === false ? 'Inaktiv' : 'Aktiv'}</td>
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
