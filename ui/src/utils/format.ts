import type {
  GuardianAlertRecord,
  GuardianAlertDecision,
  GuardianHistoryResponse,
  GuardianPolicyDecision,
  GuardianRouterCollectorState,
  GuardianSeverity,
  GuardianStatusResponse,
  GuardianSystemCollectorState,
  GuardianStateTransitionRecord,
  GuardianSnapshotRecord,
} from '../types';

const STATUS_LABELS: Record<GuardianSeverity, string> = {
  ok: 'OK',
  info: 'Info',
  warn: 'Warning',
  critical: 'Critical',
};

export function statusLabel(status?: GuardianSeverity | null): string {
  if (!status) {
    return 'Unknown';
  }
  return STATUS_LABELS[status] ?? status.toUpperCase();
}

export function statusTone(status?: GuardianSeverity | null): 'ok' | 'warn' | 'critical' | 'info' | 'neutral' {
  if (status === 'critical') return 'critical';
  if (status === 'warn') return 'warn';
  if (status === 'info') return 'info';
  if (status === 'ok') return 'ok';
  return 'neutral';
}

export function alertTone(outcome?: string | null): 'ok' | 'warn' | 'critical' | 'info' | 'neutral' {
  if (outcome === 'send') return 'ok';
  if (outcome === 'failed') return 'critical';
  if (outcome === 'suppress') return 'warn';
  return 'neutral';
}

export function formatDateTime(value?: string | null): string {
  if (!value) return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString('de-DE', {
    dateStyle: 'medium',
    timeStyle: 'medium',
  });
}

export function formatTime(value?: string | null): string {
  if (!value) return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function formatPercent(value?: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `${value.toFixed(1)}%`;
}

export function formatNumber(value?: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return new Intl.NumberFormat('de-DE').format(value);
}

export function formatBoolean(value?: boolean | null): string {
  if (value === null || value === undefined) return '—';
  return value ? 'Ja' : 'Nein';
}

export function formatRatio(value?: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return value.toFixed(2);
}

export function formatCompactReasonCodes(items?: string[] | null): string {
  if (!items || items.length === 0) return '—';
  return items.join(' · ');
}

export function formatPolicySummary(policy?: GuardianPolicyDecision | null): string {
  if (!policy) return 'No policy decision';
  return `${policy.outcome} · ${policy.summary}`;
}

export function formatAlertSummary(alerting?: GuardianAlertDecision | null): string {
  if (!alerting) return 'Alerting unavailable';
  return `${alerting.outcome} · ${alerting.summary}`;
}

export function formatRouterSummary(router: GuardianRouterCollectorState): string {
  return `${statusLabel(router.severity)} · ${router.notes?.[0] ?? '—'}`;
}

export function formatSystemSummary(system: GuardianSystemCollectorState): string {
  return `${system.hostname} · ${statusLabel(system.running_as_root ? 'ok' : 'warn')}`;
}

export function recentSnapshots(history: GuardianHistoryResponse): GuardianSnapshotRecord[] {
  return [...history.snapshots].slice(0, 6);
}

export function recentTransitions(history: GuardianHistoryResponse): GuardianStateTransitionRecord[] {
  return [...history.transitions].slice(0, 6);
}

export function recentAlerts(history: GuardianHistoryResponse): GuardianAlertRecord[] {
  return [...history.alerts].slice(0, 6);
}

export function visibilityNote(policy?: GuardianPolicyDecision | null): string {
  if (!policy) return '—';
  const notes = policy.visibility.notes.filter(Boolean);
  if (notes.length === 0) return 'No visibility limits';
  return notes.join(' · ');
}

export function coalesceText(...values: Array<string | null | undefined>): string {
  return values.find((value) => typeof value === 'string' && value.trim().length > 0)?.trim() ?? '—';
}
