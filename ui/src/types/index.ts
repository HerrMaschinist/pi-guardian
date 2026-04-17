// === Bestehende API-Typen (SOFORT NUTZBAR) ===

export interface HealthResponse {
  status: string;
}

export interface RouteRequest {
  prompt: string;
  preferred_model?: string | null;
  stream?: boolean;
}

export interface RouteResponse {
  request_id: string;
  model: string;
  response: string;
  done: boolean;
  done_reason?: string | null;
  duration_ms: number;
  fairness_review_attempted?: boolean;
  fairness_review_used?: boolean;
  fairness_risk?: string;
  fairness_review_override?: boolean;
  fairness_reasons?: string[];
  fairness_notes?: string[];
}

// === Geplante API-Typen (BACKEND ERFORDERLICH) ===

export interface RouterSettings {
  router_host: string;
  router_port: number;
  ollama_host: string;
  ollama_port: number;
  timeout: number;
  default_model: string;
  large_model: string;
  logging_level: string;
  stream_default: boolean;
  require_api_key?: boolean;
  escalation_threshold?: string;
  admin_client_name?: string;
}

export interface SettingsUpdateResponse {
  settings: RouterSettings;
  restart_requested: boolean;
  restart_performed: boolean;
  restart_message?: string | null;
  validation_warnings: string[];
}

export interface OllamaModel {
  name: string;
  size: string;
  modified_at: string;
  digest: string;
}

export interface ModelRegistryEntry {
  id: number;
  name: string;
  description: string;
  role: 'default' | 'large' | 'registered';
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ModelPullJob {
  id: number;
  model_name: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  progress_message: string;
  progress_percent?: number | null;
  requested_by?: string | null;
  result_summary?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface ClientEntry {
  id: number | string;
  name: string;
  description: string;
  active: boolean;
  allowed_ip: string;
  allowed_routes: string[];
  api_key?: string;
  enabled?: boolean;
  created_at?: string;
}

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error';
  source: string;
  message: string;
}

export interface ServiceStatus {
  service: string;
  active: boolean;
  uptime: string | null;
  pid: number | null;
  memory_usage: string | null;
  cpu_percent: number | null;
}

export interface AgentSettings {
  active?: boolean;
  preferred_model?: string | null;
  max_steps?: number;
  timeout_seconds?: number | null;
  read_only?: boolean;
  policy?: AgentPolicySettings;
  behavior?: AgentBehaviorSettings;
  personality?: AgentPersonalitySettings;
  custom_instruction?: string | null;
}

export interface AgentPolicySettings {
  allowed_tools: string[];
  allowed_skills: string[];
  allowed_actions: string[];
  read_only: boolean;
  can_propose_actions: boolean;
  can_use_logs: boolean;
  can_use_services: boolean;
  can_use_docker: boolean;
  max_steps: number;
  max_tool_calls?: number | null;
}

export interface AgentBehaviorSettings {
  analysis_mode: 'summary' | 'balanced' | 'deep';
  response_depth: 'concise' | 'balanced' | 'detailed';
  prioritization_style: 'risks_first' | 'ops_first' | 'systems_first';
  uncertainty_behavior: 'state_uncertainty' | 'ask_clarification' | 'be_conservative';
  risk_sensitivity: 'low' | 'medium' | 'high';
}

export interface AgentPersonalitySettings {
  style: 'analytical' | 'neutral' | 'supportive' | 'strict';
  tone: 'direct' | 'formal' | 'neutral';
  directness: 'low' | 'medium' | 'high';
  verbosity: 'short' | 'balanced' | 'detailed';
  technical_strictness: 'low' | 'medium' | 'high';
}

export interface AgentActivitySummary {
  last_run_id?: string | null;
  last_run_at?: string | null;
  last_status?: 'success' | 'failed' | null;
  last_model?: string | null;
  last_activity?: string | null;
  last_result_preview?: string | null;
  last_duration_ms?: number | null;
}

export interface AgentDefinition {
  name: string;
  description: string;
  agent_type?: 'system' | 'custom' | 'actor';
  allowed_tools?: string[];
  settings?: AgentSettings;
  system_prompt?: string;
  read_only?: boolean;
  enabled?: boolean;
  max_steps?: number;
  activity?: AgentActivitySummary | null;
  [key: string]: unknown;
}

export interface SkillDefinition {
  name: string;
  description: string;
  allowed_tools?: string[];
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  read_only?: boolean;
  version?: string;
  enabled?: boolean;
  [key: string]: unknown;
}

export interface ActionDefinition {
  name: string;
  description: string;
  allowed_targets?: string[];
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  read_only?: boolean;
  requires_approval?: boolean;
  version?: string;
  enabled?: boolean;
  [key: string]: unknown;
}

export interface RouteHistoryEntry {
  id: number;
  request_id: string;
  prompt_preview: string;
  model?: string | null;
  success: boolean;
  error_code?: string | null;
  client_name?: string | null;
  duration_ms?: number | null;
  fairness_review_attempted?: boolean;
  fairness_review_used?: boolean;
  fairness_risk?: string;
  fairness_review_override?: boolean;
  escalation_threshold?: string | null;
  fairness_reasons?: string[];
  fairness_notes?: string[];
  created_at: string;
  [key: string]: unknown;
}

export interface MemoryRunSummary {
  run_id: string;
  agent_name: string;
  input: string;
  used_model?: string | null;
  success: boolean;
  final_answer: string;
  started_at: string;
  finished_at?: string | null;
}

export interface MemoryStepRead {
  step_number: number;
  action_type: string;
  observation?: string | null;
  raw_payload: unknown;
  created_at: string;
}

export interface MemoryToolCallRead {
  step_number: number;
  tool_name: string;
  arguments: Record<string, unknown>;
  reason: string;
  created_at: string;
}

export interface MemoryToolResultRead {
  step_number: number;
  tool_name: string;
  success: boolean;
  output: unknown;
  error?: string | null;
  created_at: string;
}

export interface MemorySkillRunRead {
  step_number: number;
  skill_name: string;
  arguments: Record<string, unknown>;
  reason: string;
  success: boolean;
  output: unknown;
  error?: string | null;
  created_at: string;
}

export interface MemoryActionProposalRead {
  proposal_id: string;
  run_id?: string | null;
  agent_name: string;
  action_name: string;
  arguments: Record<string, unknown>;
  reason: string;
  target?: string | null;
  requires_approval: boolean;
  created_at: string;
}

export interface MemoryActionExecutionRead {
  proposal_id: string;
  run_id?: string | null;
  action_name: string;
  approved: boolean;
  success: boolean;
  output: unknown;
  error?: string | null;
  created_at: string;
}

export interface MemoryApprovalRead {
  proposal_id: string;
  approved_by?: string | null;
  approved_at: string;
  decision: string;
  comment?: string | null;
}

export interface MemoryRunDetail extends MemoryRunSummary {
  steps: MemoryStepRead[];
  tool_calls: MemoryToolCallRead[];
  tool_results: MemoryToolResultRead[];
  skill_runs: MemorySkillRunRead[];
  action_proposals: MemoryActionProposalRead[];
  action_executions: MemoryActionExecutionRead[];
  approvals: MemoryApprovalRead[];
}

export interface MemoryIncidentFindingRead {
  source_type: string;
  source_ref: string;
  finding_type: string;
  content: string;
  confidence: number;
}

export interface MemoryIncidentRead {
  id: number;
  title: string;
  summary: string;
  severity: string;
  status: string;
  related_run_id?: string | null;
  created_at: string;
  updated_at: string;
  findings: MemoryIncidentFindingRead[];
}

export interface MemoryKnowledgeEntryRead {
  id: number;
  title: string;
  pattern: string;
  probable_cause: string;
  recommended_checks: string;
  recommended_actions: string;
  confidence: number;
  confirmed: boolean;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface MemoryFeedbackEntryRead {
  id: number;
  related_run_id?: string | null;
  related_incident_id?: number | null;
  verdict: string;
  comment: string;
  created_by: string;
  created_at: string;
}

// === UI-interne Typen ===

export type Page = 'dashboard' | 'agents' | 'memory' | 'history' | 'models' | 'clients' | 'settings' | 'diagnostics' | 'logs';

export interface ApiError {
  message: string;
  status?: number;
  timestamp: string;
}

export type ConnectionState = 'connected' | 'disconnected' | 'checking' | 'error';
