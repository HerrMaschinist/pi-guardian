import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ApiRequestError,
  createAgent,
  deleteAgent,
  disableAgent,
  enableAgent,
  executeAction,
  fetchActions,
  fetchAgent,
  fetchAgentSettings,
  fetchAgents,
  fetchSkills,
  proposeAction,
  runAgent,
  updateAgent,
} from '../api/client';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import type {
  AgentBehaviorSettings,
  AgentDefinition,
  AgentPersonalitySettings,
  AgentRunResponse,
  AgentSettings,
  AgentSettingsUpdate,
  AgentUpdateRequest,
  ActionDefinition,
  ActionProposalResponse,
  ActionResult,
  SkillDefinition,
  ToolCall,
} from '../types';

type Section = 'overview' | 'config' | 'run' | 'debug' | 'manage';
type FormMode = 'create' | 'edit';

const READ_ONLY_TOOLS = ['system_status', 'docker_status', 'service_status'] as const;

const DEFAULT_BEHAVIOR: AgentBehaviorSettings = {
  analysis_mode: 'balanced',
  response_depth: 'balanced',
  prioritization_style: 'risks_first',
  uncertainty_behavior: 'state_uncertainty',
  risk_sensitivity: 'medium',
};

const DEFAULT_PERSONALITY: AgentPersonalitySettings = {
  style: 'analytical',
  tone: 'direct',
  directness: 'high',
  verbosity: 'balanced',
  technical_strictness: 'high',
};

interface AgentFormState {
  name: string;
  description: string;
  active: boolean;
  preferred_model: string;
  max_steps: string;
  timeout_seconds: string;
  read_only: boolean;
  allowed_tools: string[];
  behavior: AgentBehaviorSettings;
  personality: AgentPersonalitySettings;
  custom_instruction: string;
}

interface ActionFormState {
  agent_name: string;
  action_name: string;
  reason: string;
  target: string;
  arguments_json: string;
  approved: boolean;
}

const EMPTY_FORM: AgentFormState = {
  name: '',
  description: '',
  active: true,
  preferred_model: '',
  max_steps: '5',
  timeout_seconds: '90',
  read_only: true,
  allowed_tools: [...READ_ONLY_TOOLS],
  behavior: { ...DEFAULT_BEHAVIOR },
  personality: { ...DEFAULT_PERSONALITY },
  custom_instruction: '',
};

const EMPTY_ACTION_FORM: ActionFormState = {
  agent_name: 'service_operator',
  action_name: 'restart_service',
  reason: 'Service kontrolliert neu starten',
  target: 'pi-guardian-router',
  arguments_json: '{\n  "service_name": "pi-guardian-router"\n}',
  approved: false,
};

function cloneSettings(settings: AgentSettings): AgentSettings {
  return {
    active: settings.active,
    preferred_model: settings.preferred_model ?? '',
    max_steps: settings.max_steps,
    timeout_seconds: settings.timeout_seconds ?? 90,
    read_only: settings.read_only,
    policy: {
      allowed_tools: [...settings.policy.allowed_tools],
      allowed_skills: [...settings.policy.allowed_skills],
      allowed_actions: [...settings.policy.allowed_actions],
      read_only: settings.policy.read_only,
      can_propose_actions: settings.policy.can_propose_actions,
      can_use_logs: settings.policy.can_use_logs,
      can_use_services: settings.policy.can_use_services,
      can_use_docker: settings.policy.can_use_docker,
      max_steps: settings.policy.max_steps,
      max_tool_calls: settings.policy.max_tool_calls ?? null,
    },
    behavior: { ...settings.behavior },
    personality: { ...settings.personality },
    custom_instruction: settings.custom_instruction ?? '',
  };
}

function toForm(agent?: AgentDefinition | null): AgentFormState {
  if (!agent) {
    return { ...EMPTY_FORM, allowed_tools: [...READ_ONLY_TOOLS], behavior: { ...DEFAULT_BEHAVIOR }, personality: { ...DEFAULT_PERSONALITY } };
  }

  return {
    name: agent.name,
    description: agent.description,
    active: agent.settings.active,
    preferred_model: agent.settings.preferred_model ?? '',
    max_steps: String(agent.settings.max_steps),
    timeout_seconds: String(agent.settings.timeout_seconds ?? ''),
    read_only: agent.settings.read_only,
    allowed_tools: [...agent.allowed_tools],
    behavior: { ...agent.settings.behavior },
    personality: { ...agent.settings.personality },
    custom_instruction: agent.settings.custom_instruction ?? '',
  };
}

function parseNumber(value: string, fallback: number): number {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function isSystemAgent(agent: AgentDefinition | null | undefined): boolean {
  return agent?.agent_type === 'system';
}

function toolLabel(toolName: string): string {
  switch (toolName) {
    case 'system_status':
      return 'Systemstatus';
    case 'docker_status':
      return 'Dockerstatus';
    case 'service_status':
      return 'Dienststatus';
    default:
      return toolName;
  }
}

function actionPreset(actionName: string): Pick<ActionFormState, 'target' | 'arguments_json' | 'reason'> {
  switch (actionName) {
    case 'restart_service':
      return {
        target: 'pi-guardian-router',
        arguments_json: '{\n  "service_name": "pi-guardian-router"\n}',
        reason: 'Service kontrolliert neu starten',
      };
    case 'rerun_health_check':
      return {
        target: 'combined',
        arguments_json: '{\n  "scope": "combined"\n}',
        reason: 'Gesundheitsprüfung erneut ausführen',
      };
    case 'restart_container':
      return {
        target: 'demo-container',
        arguments_json: '{\n  "container_name": "demo-container"\n}',
        reason: 'Container-Neustart vorschlagen',
      };
    default:
      return {
        target: '',
        arguments_json: '{}',
        reason: 'Aktion prüfen',
      };
  }
}

function yesNoLabel(value: boolean): string {
  return value ? 'Ja' : 'Nein';
}

function renderPolicyPills(policy: AgentSettings['policy']) {
  return (
    <div className="agent-tool-list">
      <span className="agent-tool-pill">read_only: {yesNoLabel(policy.read_only)}</span>
      <span className="agent-tool-pill">propose: {yesNoLabel(policy.can_propose_actions)}</span>
      <span className="agent-tool-pill">logs: {yesNoLabel(policy.can_use_logs)}</span>
      <span className="agent-tool-pill">services: {yesNoLabel(policy.can_use_services)}</span>
      <span className="agent-tool-pill">docker: {yesNoLabel(policy.can_use_docker)}</span>
      <span className="agent-tool-pill">max_steps: {policy.max_steps}</span>
      <span className="agent-tool-pill">max_tool_calls: {policy.max_tool_calls ?? '—'}</span>
      <span className="agent-tool-pill">skills: {policy.allowed_skills.length}</span>
      <span className="agent-tool-pill">actions: {policy.allowed_actions.length}</span>
    </div>
  );
}

function buildPolicyFromAllowedTools(
  allowedTools: string[],
  fallback?: AgentSettings['policy']
): AgentSettings['policy'] {
  const toolSet = new Set(allowedTools);
  return {
    allowed_tools: [...allowedTools],
    allowed_skills: fallback?.allowed_skills ?? [],
    allowed_actions: fallback?.allowed_actions ?? [],
    read_only: fallback?.read_only ?? true,
    can_propose_actions: fallback?.can_propose_actions ?? false,
    can_use_logs:
      fallback?.can_use_logs ?? allowedTools.some((tool) => tool === 'router_logs' || tool.endsWith('_logs')),
    can_use_services: fallback?.can_use_services ?? toolSet.has('service_status'),
    can_use_docker: fallback?.can_use_docker ?? toolSet.has('docker_status'),
    max_steps: fallback?.max_steps ?? 5,
    max_tool_calls: fallback?.max_tool_calls ?? null,
  };
}

function renderToolCall(item: ToolCall) {
  return (
    <div className="agent-json-block">
      <div><strong>Tool:</strong> <code>{item.tool_name}</code></div>
      <div><strong>Grund:</strong> {item.reason}</div>
      <pre className="code-block" style={{ marginTop: '0.5rem' }}>{JSON.stringify(item.arguments, null, 2)}</pre>
    </div>
  );
}

function agentSummary(agent: AgentDefinition) {
  return [
    agent.agent_type === 'system' ? 'System-Agent' : agent.agent_type === 'actor' ? 'Actor-Agent' : 'Custom-Agent',
    agent.settings.read_only ? 'Read-only' : 'Write-enabled',
    agent.settings.active ? 'aktiv' : 'deaktiviert',
  ].join(' · ');
}

export function Agents() {
  const [agents, setAgents] = useState<AgentDefinition[]>([]);
  const [skills, setSkills] = useState<SkillDefinition[]>([]);
  const [actions, setActions] = useState<ActionDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<Section>('overview');
  const [selectedAgentName, setSelectedAgentName] = useState<string>('guardian_supervisor');
  const [selectedAgent, setSelectedAgent] = useState<AgentDefinition | null>(null);
  const [loadingSelected, setLoadingSelected] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deletingAgent, setDeletingAgent] = useState<string | null>(null);
  const [actionAgent, setActionAgent] = useState<string | null>(null);
  const [formMode, setFormMode] = useState<FormMode>('create');
  const [form, setForm] = useState<AgentFormState>({ ...EMPTY_FORM });
  const [formError, setFormError] = useState<string | null>(null);
  const [runAgentName, setRunAgentName] = useState('guardian_supervisor');
  const [runInput, setRunInput] = useState('Prüfe den aktuellen Systemzustand und nenne Risiken.');
  const [runPreferredModel, setRunPreferredModel] = useState('');
  const [runMaxSteps, setRunMaxSteps] = useState('5');
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState<AgentRunResponse | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [actionForm, setActionForm] = useState<ActionFormState>({ ...EMPTY_ACTION_FORM });
  const [actionResult, setActionResult] = useState<ActionProposalResponse | null>(null);
  const [actionExecutionResult, setActionExecutionResult] = useState<ActionResult | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionBusy, setActionBusy] = useState(false);

  const loadAgents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [agentData, skillData, actionData] = await Promise.all([
        fetchAgents(),
        fetchSkills(),
        fetchActions(),
      ]);
      setAgents(agentData);
      setSkills(skillData);
      setActions(actionData);
      setSelectedAgentName((current) => {
        if (agentData.some((agent) => agent.name === current)) {
          return current;
        }
        return agentData[0]?.name ?? '';
      });
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : 'Agenten konnten nicht geladen werden');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSelected = useCallback(async (agentName: string) => {
    if (!agentName) return;
    setLoadingSelected(true);
    setError(null);
    try {
      const [detail, settings] = await Promise.all([
        fetchAgent(agentName),
        fetchAgentSettings(agentName),
      ]);
      setSelectedAgent({
        ...detail,
        settings,
      });
      setFormMode('edit');
      setForm(toForm({ ...detail, settings }));
      setRunAgentName(detail.name);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : 'Agentendetails konnten nicht geladen werden');
    } finally {
      setLoadingSelected(false);
    }
  }, []);

  useEffect(() => {
    loadAgents().catch(() => {});
  }, [loadAgents]);

  useEffect(() => {
    const current = agents.find((agent) => agent.name === selectedAgentName) ?? null;
    if (current) {
      void loadSelected(current.name);
    } else if (agents.length > 0 && !selectedAgentName) {
      void loadSelected(agents[0].name);
      setSelectedAgentName(agents[0].name);
    } else if (agents.length > 0 && !current) {
      void loadSelected(agents[0].name);
      setSelectedAgentName(agents[0].name);
    } else {
      setSelectedAgent(null);
    }
  }, [agents, loadSelected, selectedAgentName]);

  const stats = useMemo(() => {
    const systemAgents = agents.filter((agent) => agent.agent_type === 'system').length;
    const customAgents = agents.filter((agent) => agent.agent_type === 'custom').length;
    const actorAgents = agents.filter((agent) => agent.agent_type === 'actor').length;
    const activeAgents = agents.filter((agent) => agent.settings.active).length;
    return { systemAgents, customAgents, actorAgents, activeAgents };
  }, [agents]);

  function selectAgent(agentName: string) {
    setSelectedAgentName(agentName);
    setActiveSection('config');
  }

  function resetCreateForm() {
    setFormMode('create');
    setForm({ ...EMPTY_FORM, allowed_tools: [...READ_ONLY_TOOLS] });
    setFormError(null);
  }

  function openCreateAgent() {
    resetCreateForm();
    setActiveSection('manage');
  }

  function openEditAgent(agent: AgentDefinition) {
    setSelectedAgentName(agent.name);
    setSelectedAgent(agent);
    setFormMode('edit');
    setForm(toForm(agent));
    setFormError(null);
    setActiveSection('config');
  }

  function updateBehavior(key: keyof AgentBehaviorSettings, value: AgentBehaviorSettings[keyof AgentBehaviorSettings]) {
    setForm((prev) => ({ ...prev, behavior: { ...prev.behavior, [key]: value } }));
  }

  function updatePersonality(key: keyof AgentPersonalitySettings, value: AgentPersonalitySettings[keyof AgentPersonalitySettings]) {
    setForm((prev) => ({ ...prev, personality: { ...prev.personality, [key]: value } }));
  }

  function toggleTool(toolName: string) {
    setForm((prev) => {
      const next = new Set(prev.allowed_tools);
      if (next.has(toolName)) next.delete(toolName);
      else next.add(toolName);
      return { ...prev, allowed_tools: Array.from(next) };
    });
  }

  async function handleSaveSelected() {
    if (!selectedAgent) return;
    setSaving(true);
    setFormError(null);
    try {
      const settings: AgentSettingsUpdate = {
        active: form.active,
        preferred_model: form.preferred_model.trim() || null,
        max_steps: parseNumber(form.max_steps, 5),
        timeout_seconds: form.timeout_seconds.trim() ? parseNumber(form.timeout_seconds, 90) : null,
        behavior: form.behavior,
        personality: form.personality,
        custom_instruction: form.custom_instruction.trim() || null,
      };

      const payload: AgentUpdateRequest = {
        description: form.description.trim(),
        settings: {
          ...cloneSettings(selectedAgent.settings),
          ...settings,
          preferred_model: settings.preferred_model ?? null,
          timeout_seconds: settings.timeout_seconds ?? null,
          policy: buildPolicyFromAllowedTools(
            selectedAgentIsSystem ? selectedAgent.allowed_tools : form.allowed_tools,
            selectedAgent.settings.policy
          ),
        } as AgentSettings,
      };

      if (!isSystemAgent(selectedAgent)) {
        payload.allowed_tools = [...form.allowed_tools];
        payload.read_only = true;
      }

      const updated = await updateAgent(selectedAgent.name, payload);
      setAgents((prev) => prev.map((agent) => (agent.name === updated.name ? updated : agent)));
      setSelectedAgent(updated);
      setForm(toForm(updated));
    } catch (err) {
      setFormError(err instanceof ApiRequestError ? err.message : 'Agent konnte nicht gespeichert werden');
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleActive(agent: AgentDefinition) {
    setActionAgent(agent.name);
    setError(null);
    try {
      const updated = agent.settings.active ? await disableAgent(agent.name) : await enableAgent(agent.name);
      setAgents((prev) => prev.map((item) => (item.name === updated.name ? updated : item)));
      if (selectedAgentName === updated.name) {
        setSelectedAgent(updated);
        setForm(toForm(updated));
      }
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : 'Status konnte nicht geändert werden');
    } finally {
      setActionAgent(null);
    }
  }

  async function handleDelete(agent: AgentDefinition) {
    if (agent.agent_type !== 'custom') return;
    const confirmed = window.confirm(`Agent "${agent.name}" wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.`);
    if (!confirmed) return;
    setDeletingAgent(agent.name);
    setError(null);
    try {
      await deleteAgent(agent.name);
      setAgents((prev) => prev.filter((item) => item.name !== agent.name));
      if (selectedAgentName === agent.name) {
        setSelectedAgentName('guardian_supervisor');
      }
      if (runAgentName === agent.name) {
        setRunAgentName('guardian_supervisor');
      }
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : 'Agent konnte nicht gelöscht werden');
    } finally {
      setDeletingAgent(null);
    }
  }

  async function handleCreateAgent() {
    if (!form.name.trim()) return;
    if (agents.some((agent) => agent.name === form.name.trim())) {
      setFormError('Agentenname existiert bereits.');
      return;
    }

    setSaving(true);
    setFormError(null);
    try {
      const created = await createAgent({
        name: form.name.trim(),
        description: form.description.trim(),
        allowed_tools: [...form.allowed_tools],
        read_only: true,
        settings: {
          active: form.active,
          preferred_model: form.preferred_model.trim() || null,
          max_steps: parseNumber(form.max_steps, 5),
          timeout_seconds: form.timeout_seconds.trim() ? parseNumber(form.timeout_seconds, 90) : null,
          read_only: true,
          policy: buildPolicyFromAllowedTools(form.allowed_tools),
          behavior: form.behavior,
          personality: form.personality,
          custom_instruction: form.custom_instruction.trim() || null,
        },
      });
      setAgents((prev) => [created, ...prev]);
      setSelectedAgentName(created.name);
      setSelectedAgent(created);
      setForm(toForm(created));
      setActiveSection('config');
    } catch (err) {
      setFormError(err instanceof ApiRequestError ? err.message : 'Agent konnte nicht angelegt werden');
    } finally {
      setSaving(false);
    }
  }

  async function handleRunAgent() {
    if (!runAgentName.trim() || !runInput.trim()) return;
    setRunning(true);
    setRunError(null);
    setRunResult(null);
    try {
      const result = await runAgent({
        agent_name: runAgentName,
        input: runInput,
        preferred_model: runPreferredModel.trim() || undefined,
        max_steps: runMaxSteps.trim() ? parseNumber(runMaxSteps, 5) : undefined,
      });
      setRunResult(result);
    } catch (err) {
      setRunError(err instanceof ApiRequestError ? err.message : 'Agenten-Testlauf fehlgeschlagen');
    } finally {
      setRunning(false);
    }
  }

  async function handleProposeAction() {
    setActionBusy(true);
    setActionError(null);
    setActionResult(null);
    setActionExecutionResult(null);
    try {
      const parsedArguments = actionForm.arguments_json.trim()
        ? (JSON.parse(actionForm.arguments_json) as Record<string, unknown>)
        : {};
      const result = await proposeAction({
        agent_name: actionForm.agent_name,
        action_name: actionForm.action_name,
        arguments: parsedArguments,
        reason: actionForm.reason.trim(),
        target: actionForm.target.trim() || null,
      });
      setActionResult(result);
      setActionForm((prev) => ({
        ...prev,
        approved: false,
      }));
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Action konnte nicht vorgeschlagen werden');
    } finally {
      setActionBusy(false);
    }
  }

  async function handleExecuteAction() {
    if (!actionResult) return;
    setActionBusy(true);
    setActionError(null);
    try {
      const result = await executeAction({
        agent_name: actionForm.agent_name,
        action_name: actionResult.proposal.action_name,
        arguments: actionResult.proposal.arguments,
        reason: actionResult.proposal.reason,
        target: actionResult.proposal.target ?? null,
        approved: actionForm.approved,
      });
      setActionExecutionResult(result);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Action konnte nicht ausgeführt werden');
    } finally {
      setActionBusy(false);
    }
  }

  const selectedAgentIsSystem = isSystemAgent(selectedAgent);
  const selectedAgentIsActor = selectedAgent?.agent_type === 'actor';

  return (
    <Layout title="Agenten">
      <div className="agent-banner">
        <div>
          <div className="agent-banner__eyebrow">PI Guardian Agent Runtime</div>
          <h2 className="agent-banner__title">Agenten-Übersicht, Konfiguration und Testlauf</h2>
          <p className="agent-banner__text">
            System-Agenten bleiben read-only und können nur innerhalb der im Backend freigegebenen Grenzen geändert werden.
          </p>
          <div className="btn-group" style={{ marginTop: '1rem' }}>
            <button className="btn" type="button" onClick={() => setActiveSection('overview')}>Übersicht</button>
            <button className="btn btn--ghost" type="button" onClick={() => setActiveSection('run')}>Testlauf</button>
            <button className="btn btn--ghost" type="button" onClick={openCreateAgent}>Neuen Agenten anlegen</button>
          </div>
        </div>
        <div className="agent-banner__stats">
          <div className="agent-stat"><span>Agenten</span><strong>{agents.length}</strong></div>
          <div className="agent-stat"><span>System</span><strong>{stats.systemAgents}</strong></div>
          <div className="agent-stat"><span>Actor</span><strong>{stats.actorAgents}</strong></div>
          <div className="agent-stat"><span>Custom</span><strong>{stats.customAgents}</strong></div>
          <div className="agent-stat"><span>Aktiv</span><strong>{stats.activeAgents}</strong></div>
        </div>
      </div>

      {error && (
        <div className="alert alert--error" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div className="agent-sections">
        {[
          ['overview', 'Übersicht'],
          ['config', 'Konfiguration'],
          ['run', 'Testlauf'],
          ['debug', 'Diagnose'],
          ['manage', 'Verwaltung'],
        ].map(([key, label]) => (
          <button
            key={key}
            className={`agent-section-tab ${activeSection === key ? 'agent-section-tab--active' : ''}`}
            onClick={() => setActiveSection(key as Section)}
            type="button"
          >
            {label}
          </button>
        ))}
      </div>

      {activeSection === 'overview' && (
        <div className="grid" style={{ gap: '1.5rem' }}>
          <Card title="Registrierte Agenten" tag="LIVE">
            {loading ? (
              <span className="text--muted">Lädt…</span>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Beschreibung</th>
                    <th>Typ</th>
                    <th>Read only</th>
                    <th>Status</th>
                    <th>Modell</th>
                    <th>Steps</th>
                    <th>Policy</th>
                    <th>Tools</th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {agents.map((agent) => (
                    <tr key={agent.name}>
                      <td>
                        <strong>{agent.name}</strong>
                        <div className="text--muted text--sm">{agent.agent_type}</div>
                      </td>
                      <td className="text--muted">{agent.description}</td>
                      <td>
                        <span className={`badge ${agent.agent_type === 'system' ? 'badge--ok' : agent.agent_type === 'actor' ? 'badge--warn' : 'badge--info'}`}>
                          <span className="badge__dot" />
                          {agent.agent_type === 'system' ? 'System' : agent.agent_type === 'actor' ? 'Actor' : 'Custom'}
                        </span>
                      </td>
                      <td>
                        <span className={agent.settings.read_only ? 'text--ok' : 'text--fail'}>
                          {agent.settings.read_only ? 'Read-only' : 'Write'}
                        </span>
                      </td>
                      <td>
                        {agent.settings.active ? (
                          <span className="badge badge--ok"><span className="badge__dot" />Aktiv</span>
                        ) : (
                          <span className="badge badge--fail"><span className="badge__dot" />Deaktiviert</span>
                        )}
                      </td>
                      <td>{agent.settings.preferred_model || '—'}</td>
                      <td>{agent.settings.max_steps}</td>
                      <td>{renderPolicyPills(agent.settings.policy)}</td>
                      <td>
                        <div className="agent-tool-list">
                          {agent.allowed_tools.map((tool) => (
                            <span key={tool} className="agent-tool-pill">{toolLabel(tool)}</span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <div className="btn-group">
                          <button className="btn btn--sm btn--ghost" type="button" onClick={() => selectAgent(agent.name)}>
                            Öffnen
                          </button>
                          <button
                            className="btn btn--sm btn--ghost"
                            type="button"
                            onClick={() => handleToggleActive(agent)}
                            disabled={actionAgent === agent.name}
                          >
                            {actionAgent === agent.name ? '…' : agent.settings.active ? 'Deaktivieren' : 'Aktivieren'}
                          </button>
                          <button
                            className="btn btn--sm btn--ghost"
                            type="button"
                            onClick={() => openEditAgent(agent)}
                          >
                            Bearbeiten
                          </button>
                          <button
                            className="btn btn--sm btn--danger"
                            type="button"
                            onClick={() => handleDelete(agent)}
                            disabled={agent.agent_type !== 'custom' || deletingAgent === agent.name}
                          >
                            {agent.agent_type !== 'custom' ? 'Geschützt' : deletingAgent === agent.name ? 'Löscht…' : 'Löschen'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {agents.length === 0 && !loading && (
                    <tr>
                      <td colSpan={10} className="text--muted">Keine Agenten registriert.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </Card>
        </div>
      )}

      {activeSection === 'config' && (
        <div className="grid grid--2">
          <Card title="Ausgewählter Agent" tag="LIVE">
            {loadingSelected && <span className="text--muted">Lädt…</span>}
            {selectedAgent ? (
              <>
                <div className="kv"><span className="kv__label">Name</span><code className="kv__value">{selectedAgent.name}</code></div>
                <div className="kv"><span className="kv__label">Typ</span><span className="kv__value">{agentSummary(selectedAgent)}</span></div>
                <div className="kv"><span className="kv__label">Beschreibung</span><span className="kv__value">{selectedAgent.description}</span></div>
                <div className="kv"><span className="kv__label">read only</span><span className="kv__value">{selectedAgent.settings.read_only ? 'Ja' : 'Nein'}</span></div>
                <div className="kv"><span className="kv__label">Aktiv</span><span className="kv__value">{selectedAgent.settings.active ? 'Ja' : 'Nein'}</span></div>
                <div className="kv"><span className="kv__label">Tools</span><span className="kv__value">{selectedAgent.allowed_tools.join(', ') || '—'}</span></div>
                <div className="kv">
                  <span className="kv__label">Policy</span>
                  <div className="kv__value">{renderPolicyPills(selectedAgent.settings.policy)}</div>
                </div>
                <div className="agent-safety-box">
                  <strong>Sicherheitsgrenzen</strong>
                  <ul className="gap-list">
                    <li>Keine Shell.</li>
                    <li>Keine Schreibzugriffe.</li>
                    <li>Keine Dienständerungen.</li>
                    <li>Keine Containeränderungen.</li>
                  </ul>
                </div>
                {selectedAgentIsActor && (
                  <div className="agent-safety-box">
                    <strong>Aktor-Modell</strong>
                    <p className="text--sm text--muted" style={{ marginTop: '0.35rem' }}>
                      Actions werden nur vorgeschlagen. Die Ausführung erfordert separate Freigabe.
                    </p>
                    <div className="agent-tool-list" style={{ marginTop: '0.5rem' }}>
                      {selectedAgent.settings.policy.allowed_actions.map((action) => (
                        <span key={action} className="agent-tool-pill">{action}</span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <span className="text--muted">Agent auswählen, um die Konfiguration zu sehen.</span>
            )}
          </Card>

          <Card title="Konfiguration bearbeiten" tag="LIVE">
            {!selectedAgent ? (
              <span className="text--muted">Kein Agent ausgewählt.</span>
            ) : (
              <>
                <div className="form-group">
                  <label className="form-label">Beschreibung</label>
                  <textarea
                    className="form-input form-input--textarea"
                    rows={3}
                    value={form.description}
                    onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
                  />
                </div>

                <div className="grid grid--2">
                  <div className="form-group">
                    <label className="form-label">Aktiv</label>
                    <div className="toggle-row">
                      <button
                        className={`btn btn--sm ${form.active ? 'btn--active' : 'btn--ghost'}`}
                        type="button"
                        onClick={() => setForm((prev) => ({ ...prev, active: true }))}
                      >
                        Aktiv
                      </button>
                      <button
                        className={`btn btn--sm ${!form.active ? 'btn--active' : 'btn--ghost'}`}
                        type="button"
                        onClick={() => setForm((prev) => ({ ...prev, active: false }))}
                      >
                        Inaktiv
                      </button>
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Read only</label>
                    <div className="form-input" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span>{form.read_only ? 'Erzwungen aktiv' : 'Erzwungen deaktiviert'}</span>
                      <span className="badge badge--warn"><span className="badge__dot" />Gesperrt</span>
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Bevorzugtes Modell</label>
                    <input
                      className="form-input"
                      value={form.preferred_model}
                      onChange={(e) => setForm((prev) => ({ ...prev, preferred_model: e.target.value }))}
                      placeholder="z.B. llama3.1"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Max Steps</label>
                    <input
                      className="form-input"
                      type="number"
                      min={1}
                      max={20}
                      value={form.max_steps}
                      onChange={(e) => setForm((prev) => ({ ...prev, max_steps: e.target.value }))}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Timeout (Sekunden)</label>
                    <input
                      className="form-input"
                      type="number"
                      min={1}
                      max={600}
                      value={form.timeout_seconds}
                      onChange={(e) => setForm((prev) => ({ ...prev, timeout_seconds: e.target.value }))}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Analysemodus</label>
                    <select
                      className="form-input"
                      value={form.behavior.analysis_mode}
                      onChange={(e) => updateBehavior('analysis_mode', e.target.value as AgentBehaviorSettings['analysis_mode'])}
                    >
                      <option value="summary">summary</option>
                      <option value="balanced">balanced</option>
                      <option value="deep">deep</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Antworttiefe</label>
                    <select
                      className="form-input"
                      value={form.behavior.response_depth}
                      onChange={(e) => updateBehavior('response_depth', e.target.value as AgentBehaviorSettings['response_depth'])}
                    >
                      <option value="concise">concise</option>
                      <option value="balanced">balanced</option>
                      <option value="detailed">detailed</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Priorisierungsstil</label>
                    <select
                      className="form-input"
                      value={form.behavior.prioritization_style}
                      onChange={(e) => updateBehavior('prioritization_style', e.target.value as AgentBehaviorSettings['prioritization_style'])}
                    >
                      <option value="risks_first">risks_first</option>
                      <option value="ops_first">ops_first</option>
                      <option value="systems_first">systems_first</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Unsicherheitsverhalten</label>
                    <select
                      className="form-input"
                      value={form.behavior.uncertainty_behavior}
                      onChange={(e) => updateBehavior('uncertainty_behavior', e.target.value as AgentBehaviorSettings['uncertainty_behavior'])}
                    >
                      <option value="state_uncertainty">state_uncertainty</option>
                      <option value="ask_clarification">ask_clarification</option>
                      <option value="be_conservative">be_conservative</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Risikoempfindlichkeit</label>
                    <select
                      className="form-input"
                      value={form.behavior.risk_sensitivity}
                      onChange={(e) => updateBehavior('risk_sensitivity', e.target.value as AgentBehaviorSettings['risk_sensitivity'])}
                    >
                      <option value="low">low</option>
                      <option value="medium">medium</option>
                      <option value="high">high</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Stil</label>
                    <select
                      className="form-input"
                      value={form.personality.style}
                      onChange={(e) => updatePersonality('style', e.target.value as AgentPersonalitySettings['style'])}
                    >
                      <option value="analytical">analytical</option>
                      <option value="neutral">neutral</option>
                      <option value="supportive">supportive</option>
                      <option value="strict">strict</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Ton</label>
                    <select
                      className="form-input"
                      value={form.personality.tone}
                      onChange={(e) => updatePersonality('tone', e.target.value as AgentPersonalitySettings['tone'])}
                    >
                      <option value="direct">direct</option>
                      <option value="formal">formal</option>
                      <option value="neutral">neutral</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Direktheit</label>
                    <select
                      className="form-input"
                      value={form.personality.directness}
                      onChange={(e) => updatePersonality('directness', e.target.value as AgentPersonalitySettings['directness'])}
                    >
                      <option value="low">low</option>
                      <option value="medium">medium</option>
                      <option value="high">high</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Ausführlichkeit</label>
                    <select
                      className="form-input"
                      value={form.personality.verbosity}
                      onChange={(e) => updatePersonality('verbosity', e.target.value as AgentPersonalitySettings['verbosity'])}
                    >
                      <option value="short">short</option>
                      <option value="balanced">balanced</option>
                      <option value="detailed">detailed</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Technische Strenge</label>
                    <select
                      className="form-input"
                      value={form.personality.technical_strictness}
                      onChange={(e) => updatePersonality('technical_strictness', e.target.value as AgentPersonalitySettings['technical_strictness'])}
                    >
                      <option value="low">low</option>
                      <option value="medium">medium</option>
                      <option value="high">high</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Custom Instruction</label>
                  <textarea
                    className="form-input form-input--textarea"
                    rows={4}
                    value={form.custom_instruction}
                    onChange={(e) => setForm((prev) => ({ ...prev, custom_instruction: e.target.value }))}
                    placeholder="Zusätzliche Anweisungen für den Agenten"
                  />
                </div>

                {!selectedAgentIsSystem && (
                  <div className="form-group">
                    <label className="form-label">Erlaubte Tools</label>
                    <div className="agent-tool-grid">
                      {READ_ONLY_TOOLS.map((tool) => (
                        <label key={tool} className="agent-tool-option">
                          <input
                            type="checkbox"
                            checked={form.allowed_tools.includes(tool)}
                            onChange={() => toggleTool(tool)}
                          />
                          <span>{toolLabel(tool)}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {selectedAgentIsSystem && (
                  <div className="agent-safety-box">
                    <strong>System-Agent</strong>
                    <p className="text--sm text--muted" style={{ marginTop: '0.35rem' }}>
                      Die Tool-Freigaben sind fest verdrahtet. Nur sichere read-only Tools sind erlaubt.
                    </p>
                    <div className="agent-tool-list" style={{ marginTop: '0.5rem' }}>
                      {selectedAgent.allowed_tools.map((tool) => (
                        <span key={tool} className="agent-tool-pill">{toolLabel(tool)}</span>
                      ))}
                    </div>
                  </div>
                )}

                {formError && (
                  <div className="alert alert--error" style={{ marginTop: '1rem' }}>
                    {formError}
                  </div>
                )}

                <div className="btn-group" style={{ marginTop: '1rem' }}>
                  <button className="btn" type="button" onClick={handleSaveSelected} disabled={saving}>
                    {saving ? 'Speichert…' : 'Konfiguration speichern'}
                  </button>
                  <button
                    className="btn btn--ghost"
                    type="button"
                    onClick={() => loadSelected(selectedAgent.name).catch(() => {})}
                    disabled={saving}
                  >
                    Neu laden
                  </button>
                </div>
              </>
            )}
          </Card>
        </div>
      )}

      {activeSection === 'run' && (
        <div className="grid grid--2">
          <Card title="Agenten-Testlauf" tag="LIVE">
            <div className="form-group">
              <label className="form-label">Agent</label>
              <select
                className="form-input"
                value={runAgentName}
                onChange={(e) => setRunAgentName(e.target.value)}
              >
                {agents.map((agent) => (
                  <option key={agent.name} value={agent.name}>
                    {agent.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Eingabetext</label>
              <textarea
                className="form-input form-input--textarea"
                rows={5}
                value={runInput}
                onChange={(e) => setRunInput(e.target.value)}
              />
            </div>
            <div className="grid grid--2">
              <div className="form-group">
                <label className="form-label">Preferred Model</label>
                <input
                  className="form-input"
                  value={runPreferredModel}
                  onChange={(e) => setRunPreferredModel(e.target.value)}
                  placeholder="optional"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Max Steps</label>
                <input
                  className="form-input"
                  type="number"
                  min={1}
                  max={20}
                  value={runMaxSteps}
                  onChange={(e) => setRunMaxSteps(e.target.value)}
                />
              </div>
            </div>
            <button className="btn" type="button" onClick={handleRunAgent} disabled={running || !runInput.trim()}>
              {running ? 'Läuft…' : 'Agent starten'}
            </button>
            {runError && <div className="alert alert--error" style={{ marginTop: '1rem' }}>{runError}</div>}
          </Card>

          <Card title="Ergebnis" tag="LIVE">
            {runResult ? (
              <>
                <div className="kv"><span className="kv__label">Agent</span><code className="kv__value">{runResult.agent_name}</code></div>
                <div className="kv"><span className="kv__label">Erfolg</span><span className="kv__value">{runResult.success ? 'Ja' : 'Nein'}</span></div>
                <div className="kv"><span className="kv__label">Modell</span><span className="kv__value">{runResult.used_model || '—'}</span></div>
                <div className="kv"><span className="kv__label">Fehler</span><span className="kv__value">{runResult.errors.length ? runResult.errors.join('; ') : '—'}</span></div>
                <div className="kv"><span className="kv__label">Proposed Action</span><span className="kv__value">{runResult.proposed_action ? String((runResult.proposed_action as Record<string, unknown>).action_name || 'vorhanden') : '—'}</span></div>
                <div style={{ marginTop: '0.75rem' }}>
                  <label className="form-label">Final Answer</label>
                  <pre className="code-block">{runResult.final_answer || '—'}</pre>
                </div>
                <div style={{ marginTop: '0.75rem' }}>
                  <label className="form-label">Tool Calls</label>
                  <div className="agent-stream">
                    {runResult.tool_calls.length > 0 ? runResult.tool_calls.map((toolCall, index) => (
                      <div key={`${toolCall.tool_name}-${index}`} className="agent-stream__item">
                        {renderToolCall(toolCall)}
                      </div>
                    )) : <span className="text--muted">Keine Tool-Aufrufe.</span>}
                  </div>
                </div>
                <div style={{ marginTop: '0.75rem' }}>
                  <label className="form-label">Schritte</label>
                  <div className="agent-stream">
                    {runResult.steps.map((step) => (
                      <div key={`${step.step_number}-${step.action}`} className="agent-stream__item">
                        <div className="kv">
                          <span className="kv__label">Schritt {step.step_number}</span>
                          <span className="kv__value">{step.action}</span>
                        </div>
                        <div className="text--sm text--muted" style={{ marginBottom: '0.5rem' }}>
                          {step.observation || '—'}
                        </div>
                        <pre className="code-block">{JSON.stringify(step.tool_call_or_response, null, 2)}</pre>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <span className="text--muted">Noch kein Testlauf ausgeführt.</span>
            )}
          </Card>
        </div>
      )}

      {activeSection === 'debug' && (
        <div className="grid grid--2">
          <Card title="Agenten-Diagnose" tag="LIVE">
            {selectedAgent ? (
              <>
                <div className="kv"><span className="kv__label">System-Agent</span><span className="kv__value">{selectedAgent.agent_type === 'system' ? 'Ja' : 'Nein'}</span></div>
                <div className="kv"><span className="kv__label">Read-only</span><span className="kv__value">{selectedAgent.settings.read_only ? 'Ja' : 'Nein'}</span></div>
                <div className="kv"><span className="kv__label">Erlaubte Tools</span><span className="kv__value">{selectedAgent.allowed_tools.join(', ')}</span></div>
                <div className="kv"><span className="kv__label">Policy</span><div className="kv__value">{renderPolicyPills(selectedAgent.settings.policy)}</div></div>
                <div className="kv"><span className="kv__label">Bevorzugtes Modell</span><span className="kv__value">{selectedAgent.settings.preferred_model || '—'}</span></div>
                <div className="kv"><span className="kv__label">Timeout</span><span className="kv__value">{selectedAgent.settings.timeout_seconds ?? '—'} s</span></div>
                <div className="kv"><span className="kv__label">Custom Instruction</span><span className="kv__value">{selectedAgent.settings.custom_instruction || '—'}</span></div>
                <div style={{ marginTop: '0.75rem' }}>
                  <label className="form-label">Raw JSON</label>
                  <pre className="code-block">{JSON.stringify(selectedAgent, null, 2)}</pre>
                </div>
              </>
            ) : (
              <span className="text--muted">Noch kein Agent geladen.</span>
            )}
          </Card>

          <Card title="Skills, Actions & Debug" tag="LIVE">
            <div className="kv"><span className="kv__label">Skills</span><span className="kv__value">{skills.length} registriert</span></div>
            <div className="agent-tool-list" style={{ marginTop: '0.5rem' }}>
              {skills.map((skill) => (
                <span key={skill.name} className="agent-tool-pill">{skill.name}</span>
              ))}
            </div>
            <div className="kv" style={{ marginTop: '1rem' }}><span className="kv__label">Actions</span><span className="kv__value">{actions.length} registriert</span></div>
            <div className="agent-tool-list" style={{ marginTop: '0.5rem' }}>
              {actions.map((action) => (
                <span key={action.name} className="agent-tool-pill">{action.name}{action.requires_approval ? ' · approval' : ''}</span>
              ))}
            </div>

            <div className="agent-safety-box" style={{ marginTop: '1rem' }}>
              <strong>Action-Vorschlag</strong>
              <div className="form-group" style={{ marginTop: '0.75rem' }}>
                <label className="form-label">Agent</label>
                <select
                  className="form-input"
                  value={actionForm.agent_name}
                  onChange={(e) => setActionForm((prev) => ({ ...prev, agent_name: e.target.value }))}
                >
                  {agents.map((agent) => (
                    <option key={agent.name} value={agent.name}>
                      {agent.name} ({agent.agent_type})
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Action</label>
                <select
                  className="form-input"
                  value={actionForm.action_name}
                  onChange={(e) => {
                    const preset = actionPreset(e.target.value);
                    setActionForm((prev) => ({
                      ...prev,
                      action_name: e.target.value,
                      target: preset.target,
                      arguments_json: preset.arguments_json,
                      reason: preset.reason,
                    }));
                  }}
                >
                  {actions.map((action) => (
                    <option key={action.name} value={action.name}>
                      {action.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Ziel</label>
                <input
                  className="form-input"
                  value={actionForm.target}
                  onChange={(e) => setActionForm((prev) => ({ ...prev, target: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Begründung</label>
                <textarea
                  className="form-input form-input--textarea"
                  rows={3}
                  value={actionForm.reason}
                  onChange={(e) => setActionForm((prev) => ({ ...prev, reason: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Arguments JSON</label>
                <textarea
                  className="form-input form-input--textarea"
                  rows={5}
                  value={actionForm.arguments_json}
                  onChange={(e) => setActionForm((prev) => ({ ...prev, arguments_json: e.target.value }))}
                />
              </div>
              <div className="btn-group">
                <button className="btn" type="button" onClick={handleProposeAction} disabled={actionBusy}>
                  {actionBusy ? 'Prüft…' : 'Action vorschlagen'}
                </button>
                <button
                  className="btn btn--ghost"
                  type="button"
                  onClick={handleExecuteAction}
                  disabled={actionBusy || !actionResult || !actionForm.approved}
                >
                  {actionBusy ? '…' : 'Freigegeben ausführen'}
                </button>
              </div>
              <label className="agent-tool-option" style={{ marginTop: '0.75rem' }}>
                <input
                  type="checkbox"
                  checked={actionForm.approved}
                  onChange={(e) => setActionForm((prev) => ({ ...prev, approved: e.target.checked }))}
                />
                <span>Ausführung freigeben</span>
              </label>
              {actionError && <div className="alert alert--error" style={{ marginTop: '0.75rem' }}>{actionError}</div>}
              {actionResult && (
                <div className="agent-json-block" style={{ marginTop: '0.75rem' }}>
                  <div><strong>Vorgeschlagene Action:</strong> <code>{actionResult.proposal.action_name}</code></div>
                  <div><strong>Freigabe:</strong> {actionResult.proposal.requires_approval ? 'erforderlich' : 'nicht erforderlich'}</div>
                  <div><strong>Grund:</strong> {actionResult.proposal.reason}</div>
                  <pre className="code-block" style={{ marginTop: '0.5rem' }}>{JSON.stringify(actionResult, null, 2)}</pre>
                </div>
              )}
              {actionExecutionResult && (
                <div className="agent-json-block" style={{ marginTop: '0.75rem' }}>
                  <strong>Ausführungsergebnis</strong>
                  <pre className="code-block" style={{ marginTop: '0.5rem' }}>{JSON.stringify(actionExecutionResult, null, 2)}</pre>
                </div>
              )}
            </div>

            <div className="agent-safety-box" style={{ marginTop: '1rem' }}>
              <strong>Debug-Hinweise</strong>
              <ul className="gap-list" style={{ marginTop: '0.5rem' }}>
                <li>System-Agenten sind nicht löschbar.</li>
                <li>Read-only bleibt serverseitig erzwungen.</li>
                <li>Nur freigegebene Skills und Actions werden akzeptiert.</li>
                <li>Agentenpersistenz wird über den Router geladen.</li>
                <li>Testläufe laufen gegen die echte Agenten-API.</li>
                <li>Actions erfordern separate Freigabe vor Ausführung.</li>
              </ul>
            </div>
          </Card>
        </div>
      )}

      {activeSection === 'manage' && (
        <div className="grid grid--2">
          <Card title="Neuen Agenten anlegen" tag="LIVE">
            <div className="form-group">
              <label className="form-label">Name</label>
              <input
                className="form-input"
                value={formMode === 'create' ? form.name : ''}
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                placeholder="z.B. maintenance_guard"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Beschreibung</label>
              <textarea
                className="form-input form-input--textarea"
                rows={3}
                value={form.description}
                onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
              />
            </div>
            <div className="grid grid--2">
              <div className="form-group">
                <label className="form-label">Aktiv</label>
                <div className="toggle-row">
                  <button
                    className={`btn btn--sm ${form.active ? 'btn--active' : 'btn--ghost'}`}
                    type="button"
                    onClick={() => setForm((prev) => ({ ...prev, active: true }))}
                  >
                    Aktiv
                  </button>
                  <button
                    className={`btn btn--sm ${!form.active ? 'btn--active' : 'btn--ghost'}`}
                    type="button"
                    onClick={() => setForm((prev) => ({ ...prev, active: false }))}
                  >
                    Inaktiv
                  </button>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Read only</label>
                <div className="form-input" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>Erzwungen</span>
                  <span className="badge badge--warn"><span className="badge__dot" />True</span>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Bevorzugtes Modell</label>
                <input
                  className="form-input"
                  value={form.preferred_model}
                  onChange={(e) => setForm((prev) => ({ ...prev, preferred_model: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Max Steps</label>
                <input
                  className="form-input"
                  type="number"
                  min={1}
                  max={20}
                  value={form.max_steps}
                  onChange={(e) => setForm((prev) => ({ ...prev, max_steps: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Timeout (Sekunden)</label>
                <input
                  className="form-input"
                  type="number"
                  min={1}
                  max={600}
                  value={form.timeout_seconds}
                  onChange={(e) => setForm((prev) => ({ ...prev, timeout_seconds: e.target.value }))}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Erlaubte Tools</label>
              <div className="agent-tool-grid">
                {READ_ONLY_TOOLS.map((tool) => (
                  <label key={tool} className="agent-tool-option">
                    <input
                      type="checkbox"
                      checked={form.allowed_tools.includes(tool)}
                      onChange={() => toggleTool(tool)}
                    />
                    <span>{toolLabel(tool)}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="grid grid--2">
              <div className="form-group">
                <label className="form-label">Analysemodus</label>
                <select className="form-input" value={form.behavior.analysis_mode} onChange={(e) => updateBehavior('analysis_mode', e.target.value as AgentBehaviorSettings['analysis_mode'])}>
                  <option value="summary">summary</option>
                  <option value="balanced">balanced</option>
                  <option value="deep">deep</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Antworttiefe</label>
                <select className="form-input" value={form.behavior.response_depth} onChange={(e) => updateBehavior('response_depth', e.target.value as AgentBehaviorSettings['response_depth'])}>
                  <option value="concise">concise</option>
                  <option value="balanced">balanced</option>
                  <option value="detailed">detailed</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Priorisierungsstil</label>
                <select className="form-input" value={form.behavior.prioritization_style} onChange={(e) => updateBehavior('prioritization_style', e.target.value as AgentBehaviorSettings['prioritization_style'])}>
                  <option value="risks_first">risks_first</option>
                  <option value="ops_first">ops_first</option>
                  <option value="systems_first">systems_first</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Unsicherheitsverhalten</label>
                <select className="form-input" value={form.behavior.uncertainty_behavior} onChange={(e) => updateBehavior('uncertainty_behavior', e.target.value as AgentBehaviorSettings['uncertainty_behavior'])}>
                  <option value="state_uncertainty">state_uncertainty</option>
                  <option value="ask_clarification">ask_clarification</option>
                  <option value="be_conservative">be_conservative</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Risikoempfindlichkeit</label>
                <select className="form-input" value={form.behavior.risk_sensitivity} onChange={(e) => updateBehavior('risk_sensitivity', e.target.value as AgentBehaviorSettings['risk_sensitivity'])}>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Stil</label>
                <select className="form-input" value={form.personality.style} onChange={(e) => updatePersonality('style', e.target.value as AgentPersonalitySettings['style'])}>
                  <option value="analytical">analytical</option>
                  <option value="neutral">neutral</option>
                  <option value="supportive">supportive</option>
                  <option value="strict">strict</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Ton</label>
                <select className="form-input" value={form.personality.tone} onChange={(e) => updatePersonality('tone', e.target.value as AgentPersonalitySettings['tone'])}>
                  <option value="direct">direct</option>
                  <option value="formal">formal</option>
                  <option value="neutral">neutral</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Direktheit</label>
                <select className="form-input" value={form.personality.directness} onChange={(e) => updatePersonality('directness', e.target.value as AgentPersonalitySettings['directness'])}>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Ausführlichkeit</label>
                <select className="form-input" value={form.personality.verbosity} onChange={(e) => updatePersonality('verbosity', e.target.value as AgentPersonalitySettings['verbosity'])}>
                  <option value="short">short</option>
                  <option value="balanced">balanced</option>
                  <option value="detailed">detailed</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Technische Strenge</label>
                <select className="form-input" value={form.personality.technical_strictness} onChange={(e) => updatePersonality('technical_strictness', e.target.value as AgentPersonalitySettings['technical_strictness'])}>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Custom Instruction</label>
              <textarea
                className="form-input form-input--textarea"
                rows={4}
                value={form.custom_instruction}
                onChange={(e) => setForm((prev) => ({ ...prev, custom_instruction: e.target.value }))}
              />
            </div>

            {formError && <div className="alert alert--error" style={{ marginBottom: '1rem' }}>{formError}</div>}

            <div className="btn-group">
              <button className="btn" type="button" onClick={handleCreateAgent} disabled={saving}>
                {saving ? 'Anlegen…' : 'Agent anlegen'}
              </button>
              <button className="btn btn--ghost" type="button" onClick={resetCreateForm}>
                Zurücksetzen
              </button>
            </div>
          </Card>

          <Card title="Verwaltung" tag="LIVE">
            <div className="form-group">
              <label className="form-label">Vorhandene Agenten</label>
              <div className="agent-management-list">
                {agents.map((agent) => (
                  <div key={agent.name} className="agent-management-item">
                    <div>
                      <strong>{agent.name}</strong>
                      <div className="text--sm text--muted">{agent.description}</div>
                    </div>
                    <div className="btn-group">
                      <button className="btn btn--sm btn--ghost" type="button" onClick={() => openEditAgent(agent)}>
                        Bearbeiten
                      </button>
                      <button className="btn btn--sm btn--ghost" type="button" onClick={() => handleToggleActive(agent)} disabled={actionAgent === agent.name}>
                        {agent.settings.active ? 'Deaktivieren' : 'Aktivieren'}
                      </button>
                      <button className="btn btn--sm btn--danger" type="button" onClick={() => handleDelete(agent)} disabled={agent.agent_type !== 'custom' || deletingAgent === agent.name}>
                        {agent.agent_type !== 'custom' ? 'Geschützt' : 'Löschen'}
                      </button>
                    </div>
                  </div>
                ))}
                {agents.length === 0 && (
                  <div className="text--muted">Keine Agenten vorhanden.</div>
                )}
              </div>
            </div>
            <div className="agent-safety-box">
              <strong>Validierung</strong>
              <ul className="gap-list" style={{ marginTop: '0.5rem' }}>
                <li>Namestruktur wird vom Backend validiert.</li>
                <li>Tool-Freigaben sind auf read-only Tools begrenzt.</li>
                <li>System-Agenten können nicht gelöscht werden.</li>
              </ul>
            </div>
          </Card>
        </div>
      )}
    </Layout>
  );
}
