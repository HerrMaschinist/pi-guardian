export type GuardianSeverity = 'ok' | 'info' | 'warn' | 'critical';
export type GuardianSignalSource = 'router' | 'system' | 'storage' | 'journal' | 'external';
export type GuardianPolicyOutcome =
  | 'ignore'
  | 'log_only'
  | 'observe'
  | 'alert_candidate'
  | 'action_candidate'
  | 'deferred';
export type GuardianAlertOutcome = 'send' | 'suppress' | 'failed';
export type GuardianAlertKind = 'none' | 'warning' | 'critical' | 'recovery' | 'visibility';

export interface GuardianEvaluationReason {
  code: string;
  summary: string;
  severity: GuardianSeverity;
  source: GuardianSignalSource;
  detail?: string | null;
  evidence?: Record<string, unknown>;
  created_at?: string;
}

export interface GuardianRouterAccessState {
  value: 'reachable' | 'unreachable' | 'auth_required' | 'partial' | 'unknown';
}

export interface GuardianRouterReadinessState {
  value: 'healthy' | 'degraded' | 'incomplete' | 'invalid' | 'unavailable' | 'auth_required' | 'unknown';
}

export interface GuardianRouterHealthPayload {
  status?: string | null;
  service?: string | null;
  version?: string | null;
  router_busy?: boolean | null;
  ollama_reachable?: boolean | null;
  configured_models?: Record<string, unknown> | null;
}

export interface GuardianRouterServiceStatusPayload {
  service?: string | null;
  active?: boolean | null;
  uptime?: string | null;
  pid?: number | null;
  memory_usage?: string | null;
  cpu_percent?: number | null;
}

export interface GuardianFinding {
  code: string;
  summary: string;
  severity: GuardianSeverity;
  source: GuardianSignalSource;
  detail?: string | null;
  evidence?: Record<string, unknown>;
  created_at?: string;
}

export interface GuardianRouterProbe {
  checked_at?: string;
  status?: GuardianSeverity;
  action?: string;
  reachable?: boolean;
  service_active?: boolean | null;
  health_result?: {
    endpoint?: string;
    ok?: boolean;
    status_code?: number | null;
    error_kind?: string | null;
    error_message?: string | null;
    payload?: Record<string, unknown> | null;
  } | null;
  service_status_result?: {
    endpoint?: string;
    ok?: boolean;
    status_code?: number | null;
    error_kind?: string | null;
    error_message?: string | null;
    payload?: Record<string, unknown> | null;
  } | null;
  health?: GuardianRouterHealthPayload | null;
  service_status?: GuardianRouterServiceStatusPayload | null;
  findings?: GuardianFinding[];
  errors?: string[];
  router_base_url?: string;
  health_path?: string;
  status_path?: string;
}

export interface GuardianRouterCollectorState {
  checked_at: string;
  base_url: string;
  health_path: string;
  status_path: string;
  access_state: 'reachable' | 'unreachable' | 'auth_required' | 'partial' | 'unknown';
  readiness_state: 'healthy' | 'degraded' | 'incomplete' | 'invalid' | 'unavailable' | 'auth_required' | 'unknown';
  severity: GuardianSeverity;
  healthy: boolean;
  degraded: boolean;
  incomplete: boolean;
  auth_required: boolean;
  reachable: boolean;
  health: GuardianRouterHealthPayload | null;
  service_status: GuardianRouterServiceStatusPayload | null;
  findings: GuardianFinding[];
  notes: string[];
  probe: GuardianRouterProbe;
}

export interface GuardianSystemCollectorState {
  checked_at: string;
  hostname: string;
  running_as_root: boolean;
  process_pid: number;
  process_name: string;
  process_uptime_seconds?: number | null;
  cpu_count?: number | null;
  cpu_usage_percent?: number | null;
  load_avg_1m?: number | null;
  load_avg_5m?: number | null;
  load_avg_15m?: number | null;
  cpu_load_ratio_1m?: number | null;
  memory_total_bytes?: number | null;
  memory_available_bytes?: number | null;
  memory_used_bytes?: number | null;
  memory_usage_percent?: number | null;
  disk_mountpoint?: string;
  disk_total_bytes?: number | null;
  disk_free_bytes?: number | null;
  disk_used_bytes?: number | null;
  disk_usage_percent?: number | null;
  temperature_c?: number | null;
  temperature_source?: string | null;
  notes: string[];
  errors: string[];
}

export interface GuardianRouterEvaluation {
  status: GuardianSeverity;
  summary: string;
  checked_at: string;
  reasons: GuardianEvaluationReason[];
  router: GuardianRouterCollectorState;
}

export interface GuardianSystemEvaluation {
  status: GuardianSeverity;
  summary: string;
  checked_at: string;
  reasons: GuardianEvaluationReason[];
  system: GuardianSystemCollectorState;
}

export interface GuardianOverviewEvaluation {
  status: GuardianSeverity;
  summary: string;
  checked_at: string;
  reasons: GuardianEvaluationReason[];
  router: GuardianRouterEvaluation;
  system: GuardianSystemEvaluation;
}

export interface GuardianPersistenceReceipt {
  ok: boolean;
  database_path: string;
  stored_at: string;
  snapshot_id?: number | null;
  transition_id?: number | null;
  changed: boolean;
  previous_status?: GuardianSeverity | null;
  current_status?: GuardianSeverity | null;
  error?: string | null;
}

export interface GuardianPolicyVisibility {
  auth_limited: boolean;
  privilege_limited: boolean;
  data_limited: boolean;
  reduced_confidence: boolean;
  notes: string[];
}

export interface GuardianPolicyReason {
  code: string;
  summary: string;
  severity: GuardianSeverity;
  source: GuardianSignalSource;
  detail?: string | null;
  evidence?: Record<string, unknown>;
  created_at?: string;
}

export interface GuardianPolicyDecision {
  outcome: GuardianPolicyOutcome;
  relevance: GuardianSeverity;
  checked_at: string;
  summary: string;
  reasons: GuardianPolicyReason[];
  visibility: GuardianPolicyVisibility;
  changed: boolean;
  transition_relevant: boolean;
  candidate_alert: boolean;
  candidate_action: boolean;
  deferred: boolean;
  confidence: number;
  current_status: GuardianSeverity;
  previous_status?: GuardianSeverity | null;
  snapshot_id?: number | null;
  transition_id?: number | null;
  persistence_ok: boolean;
  context: Record<string, unknown>;
}

export interface GuardianAlertSendResult {
  ok: boolean;
  chat_id?: string | null;
  message_id?: number | null;
  status_code?: number | null;
  sent_at: string;
  error?: string | null;
}

export interface GuardianAlertDecision {
  outcome: GuardianAlertOutcome;
  alert_kind: GuardianAlertKind;
  should_send: boolean;
  sent: boolean;
  suppressed: boolean;
  summary: string;
  reason_codes: string[];
  alert_key: string;
  dedupe_key: string;
  cooldown_seconds: number;
  cooldown_remaining_seconds?: number | null;
  policy_outcome: GuardianPolicyOutcome;
  current_status: GuardianSeverity;
  previous_status?: GuardianSeverity | null;
  changed: boolean;
  transition_relevant: boolean;
  telegram_ready: boolean;
  telegram_ready_reason: string;
  policy_visibility: GuardianPolicyVisibility;
  message_text: string;
  send_result?: GuardianAlertSendResult | null;
  error?: string | null;
  context: Record<string, unknown>;
}

export interface GuardianSnapshotRecord {
  id: number;
  checked_at: string;
  guardian_status: GuardianSeverity;
  router_status: GuardianSeverity;
  system_status: GuardianSeverity;
  overview_summary: string;
  router_summary: string;
  system_summary: string;
  overview_reason_codes: string[];
  router_reason_codes: string[];
  system_reason_codes: string[];
  router_access_state: string;
  router_readiness_state: string;
  router_reachable: boolean;
  router_auth_required: boolean;
  system_running_as_root: boolean;
  system_cpu_usage_percent?: number | null;
  system_memory_usage_percent?: number | null;
  system_disk_usage_percent?: number | null;
  system_temperature_c?: number | null;
  evidence: Record<string, unknown>;
  stored_at: string;
}

export interface GuardianStateTransitionRecord {
  id: number;
  created_at: string;
  previous_snapshot_id?: number | null;
  current_snapshot_id: number;
  from_status: GuardianSeverity;
  to_status: GuardianSeverity;
  reason_codes: string[];
  summary: string;
  evidence: Record<string, unknown>;
}

export interface GuardianAlertRecord {
  id: number;
  checked_at: string;
  sent_at?: string | null;
  alert_key: string;
  dedupe_key: string;
  alert_kind: string;
  outcome: string;
  should_send: boolean;
  sent: boolean;
  suppressed_reason?: string | null;
  current_status: GuardianSeverity;
  previous_status?: GuardianSeverity | null;
  policy_outcome: string;
  changed: boolean;
  transition_relevant: boolean;
  cooldown_seconds: number;
  cooldown_remaining_seconds?: number | null;
  telegram_ready: boolean;
  telegram_ready_reason: string;
  telegram_chat_id?: string | null;
  telegram_message_id?: number | null;
  telegram_error?: string | null;
  reason_codes: string[];
  summary: string;
  message_text: string;
  evidence: Record<string, unknown>;
}

export interface GuardianHistoryResponse {
  checked_at: string;
  limit: number;
  snapshots: GuardianSnapshotRecord[];
  transitions: GuardianStateTransitionRecord[];
  alerts: GuardianAlertRecord[];
}

export interface GuardianStatusResponse {
  status: GuardianSeverity;
  component: string;
  version: string;
  checked_at: string;
  router: GuardianRouterCollectorState;
  router_evaluation: GuardianRouterEvaluation;
  system: GuardianSystemCollectorState;
  system_evaluation: GuardianSystemEvaluation;
  evaluation: GuardianOverviewEvaluation;
  persistence?: GuardianPersistenceReceipt | null;
  policy?: GuardianPolicyDecision | null;
  alerting?: GuardianAlertDecision | null;
}

export interface GuardianDashboardPayload {
  status: GuardianStatusResponse;
  history: GuardianHistoryResponse;
}
