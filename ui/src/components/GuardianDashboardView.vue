<script setup lang="ts">
import { computed } from 'vue';

import { CONFIG } from '../config';
import { useGuardianDashboard } from '../composables/useGuardianDashboard';
import {
  alertTone,
  formatBoolean,
  formatCompactReasonCodes,
  formatDateTime,
  formatPercent,
  formatRatio,
  formatTime,
  recentAlerts,
  recentSnapshots,
  recentTransitions,
  statusLabel,
  statusTone,
} from '../utils/format';
import type { GuardianHistoryResponse } from '../types';
import MetricTile from './MetricTile.vue';
import ReasonChips from './ReasonChips.vue';
import SectionCard from './SectionCard.vue';
import StatusPill from './StatusPill.vue';

interface Props {
  apiBaseUrl?: string;
  historyLimit?: number;
  refreshIntervalMs?: number;
}

const props = withDefaults(defineProps<Props>(), {
  apiBaseUrl: CONFIG.apiBaseUrl,
  historyLimit: CONFIG.historyLimit,
  refreshIntervalMs: CONFIG.refreshIntervalMs,
});

const {
  status,
  history,
  loading,
  refreshing,
  errorMessage,
  statusError,
  historyError,
  lastUpdatedAt,
  autoRefreshEnabled,
  refresh,
  setAutoRefreshEnabled,
} = useGuardianDashboard({
  apiBaseUrl: props.apiBaseUrl,
  historyLimit: props.historyLimit,
  refreshIntervalMs: props.refreshIntervalMs,
});

const emptyHistory: GuardianHistoryResponse = {
  checked_at: '',
  limit: 0,
  snapshots: [],
  transitions: [],
  alerts: [],
};

const current = computed(() => status.value);
const currentHistory = computed(() => history.value);
const router = computed(() => current.value?.router ?? null);
const system = computed(() => current.value?.system ?? null);
const policy = computed(() => current.value?.policy ?? null);
const alerting = computed(() => current.value?.alerting ?? null);
const latestSnapshot = computed(() => currentHistory.value?.snapshots?.[0] ?? null);
const latestTransition = computed(() => currentHistory.value?.transitions?.[0] ?? null);
const latestAlert = computed(() => currentHistory.value?.alerts?.[0] ?? null);
const recentSnapshotItems = computed(() => recentSnapshots(currentHistory.value ?? emptyHistory));
const recentTransitionItems = computed(() => recentTransitions(currentHistory.value ?? emptyHistory));
const recentAlertItems = computed(() => recentAlerts(currentHistory.value ?? emptyHistory));

function autoRefreshLabel() {
  return autoRefreshEnabled.value ? 'Auto-Refresh an' : 'Auto-Refresh aus';
}

function toggleAutoRefresh() {
  setAutoRefreshEnabled(!autoRefreshEnabled.value);
}

function compactReasonCodes(items?: string[] | null) {
  return formatCompactReasonCodes(items ?? []);
}

function visibilityText() {
  if (!policy.value) {
    return '—';
  }
  const notes = policy.value.visibility.notes.filter(Boolean);
  return notes.length > 0 ? notes.join(' · ') : 'Keine Sichtgrenzen';
}

function alertStatusTone(value?: string | null) {
  return alertTone(value);
}

function confidenceLabel() {
  if (!policy.value) return '—';
  return `${Math.round(policy.value.confidence * 100)}%`;
}
</script>

<template>
  <div class="dashboard-shell">
    <header class="dashboard-hero">
      <div class="dashboard-hero__copy">
        <p class="dashboard-kicker">PI Guardian</p>
        <h1 class="dashboard-title">Operative Sicht auf Router, System, Policy und Alerting</h1>
        <p class="dashboard-intro">
          Read-only Kontrolloberfläche für den aktuellen Guardian-Stand. Die UI zeigt,
          was der Guardian sieht, bewertet, persistiert und wie er operative Relevanz einordnet.
        </p>
      </div>

      <div class="dashboard-hero__status">
        <StatusPill
          :tone="statusTone(current?.status)"
          :label="statusLabel(current?.status)"
        />
        <div class="dashboard-hero__summary">
          {{ current?.evaluation?.summary ?? 'Awaiting Guardian data' }}
        </div>
        <dl class="hero-metadata">
          <div>
            <dt>Aktualisiert</dt>
            <dd>{{ formatDateTime(lastUpdatedAt) }}</dd>
          </div>
          <div>
            <dt>API</dt>
            <dd>{{ props.apiBaseUrl }}</dd>
          </div>
          <div>
            <dt>Refresh</dt>
            <dd>{{ autoRefreshLabel() }}</dd>
          </div>
        </dl>
      </div>
    </header>

    <nav class="quick-nav" aria-label="Guardian sections">
      <a href="#overview">Overview</a>
      <a href="#router">Router</a>
      <a href="#system">System</a>
      <a href="#policy">Policy</a>
      <a href="#alerting">Alerting</a>
      <a href="#history">Verlauf</a>
    </nav>

    <div v-if="errorMessage" class="status-banner status-banner--warn">
      <strong>Teilweise eingeschränkte Datenlage:</strong> {{ errorMessage }}
    </div>

    <div v-if="statusError" class="status-banner status-banner--critical">
      <strong>Status-Fehler:</strong> {{ statusError }}
    </div>

    <div class="dashboard-toolbar">
      <button class="button button--primary" type="button" @click="refresh">
        {{ refreshing ? 'Aktualisiere…' : 'Aktualisieren' }}
      </button>
      <button class="button button--ghost" type="button" @click="toggleAutoRefresh">
        {{ autoRefreshEnabled ? 'Auto-Refresh deaktivieren' : 'Auto-Refresh aktivieren' }}
      </button>
      <span class="toolbar-hint">
        Letzte erfolgreiche Aktualisierung:
        <strong>{{ formatDateTime(current?.checked_at) }}</strong>
      </span>
      <span class="toolbar-hint">
        Letzter Verlaufsscan:
        <strong>{{ formatDateTime(currentHistory?.checked_at) }}</strong>
      </span>
    </div>

    <section id="overview" class="dashboard-section">
      <SectionCard
        title="Overview"
        eyebrow="Gesamtbild"
        subtitle="Der Guardian-Status, die operative Einordnung und die sofort sichtbaren Risiken."
      >
        <template #actions>
          <StatusPill :tone="statusTone(current?.status)" :label="statusLabel(current?.status)" />
        </template>

        <div class="metric-grid metric-grid--4">
          <MetricTile
            label="Guardian"
            :value="statusLabel(current?.status)"
            :tone="statusTone(current?.status)"
            :hint="current?.evaluation?.summary ?? 'Keine Daten'"
          />
          <MetricTile
            label="Policy"
            :value="policy?.outcome ?? '—'"
            :tone="policy?.outcome === 'action_candidate' ? 'critical' : policy?.outcome === 'alert_candidate' ? 'warn' : 'neutral'"
            :hint="policy?.summary ?? 'Keine Policy-Daten'"
          />
          <MetricTile
            label="Alerting"
            :value="alerting?.outcome ?? '—'"
            :tone="alertStatusTone(alerting?.outcome ?? null)"
            :hint="alerting?.summary ?? 'Keine Alert-Daten'"
          />
          <MetricTile
            label="Sichtgrenzen"
            :value="policy?.visibility.reduced_confidence ? 'Eingeschränkt' : 'Klar'"
            :tone="policy?.visibility.reduced_confidence ? 'warn' : 'ok'"
            :hint="visibilityText()"
          />
        </div>

        <div class="overview-strip">
          <div class="overview-strip__item">
            <span class="overview-strip__label">Komponente</span>
            <span class="overview-strip__value">{{ current?.component ?? '—' }}</span>
          </div>
          <div class="overview-strip__item">
            <span class="overview-strip__label">Version</span>
            <span class="overview-strip__value">{{ current?.version ?? '—' }}</span>
          </div>
          <div class="overview-strip__item">
            <span class="overview-strip__label">Letzter Wechsel</span>
            <span class="overview-strip__value">
              {{ latestTransition ? `${statusLabel(latestTransition.from_status)} → ${statusLabel(latestTransition.to_status)}` : 'Kein Wechsel' }}
            </span>
          </div>
          <div class="overview-strip__item">
            <span class="overview-strip__label">Letzter Alert</span>
            <span class="overview-strip__value">
              {{ latestAlert ? `${latestAlert.outcome} · ${latestAlert.alert_kind}` : 'Kein Alert' }}
            </span>
          </div>
        </div>
      </SectionCard>
    </section>

    <div class="dashboard-grid dashboard-grid--2">
      <section id="router" class="dashboard-section">
        <SectionCard
          title="Router"
          eyebrow="Beobachtung"
          subtitle="Lesbare Sicht auf Erreichbarkeit, Auth-Grenzen und den normierten Router-Zustand."
        >
          <template #actions>
            <StatusPill :tone="router ? statusTone(router.severity) : 'neutral'" :label="router ? statusLabel(router.severity) : 'Unknown'" />
          </template>

          <div v-if="router" class="kv-grid">
            <div>
              <span class="kv-label">Erreichbar</span>
              <span class="kv-value">{{ formatBoolean(router.reachable) }}</span>
            </div>
            <div>
              <span class="kv-label">Access State</span>
              <span class="kv-value">{{ router.access_state }}</span>
            </div>
            <div>
              <span class="kv-label">Readiness</span>
              <span class="kv-value">{{ router.readiness_state }}</span>
            </div>
            <div>
              <span class="kv-label">auth_required</span>
              <span class="kv-value">{{ formatBoolean(router.auth_required) }}</span>
            </div>
            <div>
              <span class="kv-label">healthy</span>
              <span class="kv-value">{{ formatBoolean(router.healthy) }}</span>
            </div>
            <div>
              <span class="kv-label">degraded</span>
              <span class="kv-value">{{ formatBoolean(router.degraded) }}</span>
            </div>
            <div>
              <span class="kv-label">incomplete</span>
              <span class="kv-value">{{ formatBoolean(router.incomplete) }}</span>
            </div>
            <div>
              <span class="kv-label">Basis-URL</span>
              <span class="kv-value">{{ router.base_url }}</span>
            </div>
          </div>

          <div class="section-copy">
            <p class="section-copy__summary">{{ router?.notes?.[0] ?? 'Keine Router-Notizen.' }}</p>
          </div>

          <div class="section-block">
            <h3 class="section-block__title">Router-Summary</h3>
            <p class="section-copy__summary">{{ router?.probe?.health?.status ?? router?.probe?.health_result?.error_message ?? '—' }}</p>
          </div>

          <div class="section-block">
            <h3 class="section-block__title">Reason-Codes</h3>
            <ReasonChips :items="router?.findings?.map((item) => item.code) ?? []" />
          </div>
        </SectionCard>
      </section>

      <section id="system" class="dashboard-section">
        <SectionCard
          title="System"
          eyebrow="Host-Sicht"
          subtitle="Normierte lokale Systemdaten mit Root- und Privilegienkontext."
        >
          <template #actions>
            <StatusPill :tone="system ? statusTone(system.running_as_root ? 'ok' : 'warn') : 'neutral'" :label="system ? (system.running_as_root ? 'Root' : 'Nicht root') : 'Unknown'" />
          </template>

          <div v-if="system" class="kv-grid">
            <div>
              <span class="kv-label">Hostname</span>
              <span class="kv-value">{{ system.hostname }}</span>
            </div>
            <div>
              <span class="kv-label">running_as_root</span>
              <span class="kv-value">{{ formatBoolean(system.running_as_root) }}</span>
            </div>
            <div>
              <span class="kv-label">CPU</span>
              <span class="kv-value">{{ formatPercent(system.cpu_usage_percent) }}</span>
            </div>
            <div>
              <span class="kv-label">RAM</span>
              <span class="kv-value">{{ formatPercent(system.memory_usage_percent) }}</span>
            </div>
            <div>
              <span class="kv-label">Disk</span>
              <span class="kv-value">{{ formatPercent(system.disk_usage_percent) }}</span>
            </div>
            <div>
              <span class="kv-label">Temperatur</span>
              <span class="kv-value">{{ system.temperature_c !== null && system.temperature_c !== undefined ? `${system.temperature_c.toFixed(1)} °C` : '—' }}</span>
            </div>
            <div>
              <span class="kv-label">Load 1m</span>
              <span class="kv-value">{{ formatRatio(system.load_avg_1m) }}</span>
            </div>
            <div>
              <span class="kv-label">Prozess</span>
              <span class="kv-value">{{ system.process_name }} #{{ system.process_pid }}</span>
            </div>
          </div>

          <div class="section-copy">
            <p class="section-copy__summary">{{ system?.notes?.[0] ?? 'Keine System-Notizen.' }}</p>
          </div>

          <div class="section-block">
            <h3 class="section-block__title">System-Summary</h3>
            <p class="section-copy__summary">{{ system?.errors?.length ? system.errors[0] : 'Systemdaten liegen ohne Fehler vor.' }}</p>
          </div>

          <div class="section-block">
            <h3 class="section-block__title">Reason-Codes</h3>
            <ReasonChips :items="current?.system_evaluation?.reasons?.map((item) => item.code) ?? []" />
          </div>
        </SectionCard>
      </section>
    </div>

    <div class="dashboard-grid dashboard-grid--2">
      <section id="policy" class="dashboard-section">
        <SectionCard
          title="Policy"
          eyebrow="Operative Einordnung"
          subtitle="Die Regel-Ebene interpretiert die Bewertung, ohne etwas auszuführen."
        >
          <template #actions>
            <StatusPill
              :tone="policy ? (policy.outcome === 'action_candidate' ? 'critical' : policy.outcome === 'alert_candidate' ? 'warn' : policy.outcome === 'observe' ? 'info' : 'neutral') : 'neutral'"
              :label="policy?.outcome ?? 'Unknown'"
            />
          </template>

          <div v-if="policy" class="kv-grid">
            <div>
              <span class="kv-label">Outcome</span>
              <span class="kv-value">{{ policy.outcome }}</span>
            </div>
            <div>
              <span class="kv-label">Relevance</span>
              <span class="kv-value">{{ policy.relevance }}</span>
            </div>
            <div>
              <span class="kv-label">changed</span>
              <span class="kv-value">{{ formatBoolean(policy.changed) }}</span>
            </div>
            <div>
              <span class="kv-label">transition_relevant</span>
              <span class="kv-value">{{ formatBoolean(policy.transition_relevant) }}</span>
            </div>
            <div>
              <span class="kv-label">candidate_alert</span>
              <span class="kv-value">{{ formatBoolean(policy.candidate_alert) }}</span>
            </div>
            <div>
              <span class="kv-label">candidate_action</span>
              <span class="kv-value">{{ formatBoolean(policy.candidate_action) }}</span>
            </div>
            <div>
              <span class="kv-label">deferred</span>
              <span class="kv-value">{{ formatBoolean(policy.deferred) }}</span>
            </div>
            <div>
              <span class="kv-label">Confidence</span>
              <span class="kv-value">{{ confidenceLabel() }}</span>
            </div>
          </div>

          <div class="section-copy">
            <p class="section-copy__summary">{{ policy?.summary ?? 'Keine Policy-Daten.' }}</p>
          </div>

          <div class="section-block">
            <h3 class="section-block__title">Sichtgrenzen</h3>
            <div class="status-notes">
              <StatusPill :tone="policy?.visibility.auth_limited ? 'warn' : 'ok'" :label="policy?.visibility.auth_limited ? 'auth-limited' : 'auth ok'" />
              <StatusPill :tone="policy?.visibility.privilege_limited ? 'warn' : 'ok'" :label="policy?.visibility.privilege_limited ? 'privilege-limited' : 'root ok'" />
              <StatusPill :tone="policy?.visibility.data_limited ? 'warn' : 'ok'" :label="policy?.visibility.data_limited ? 'data-limited' : 'data ok'" />
            </div>
            <p class="section-copy__summary">{{ visibilityText() }}</p>
          </div>

          <div class="section-block">
            <h3 class="section-block__title">Reason-Codes</h3>
            <ReasonChips :items="policy?.reasons?.map((item) => item.code) ?? []" />
          </div>
        </SectionCard>
      </section>

      <section id="alerting" class="dashboard-section">
        <SectionCard
          title="Alerting"
          eyebrow="Telegram"
          subtitle="Senden oder unterdrücken auf Basis der Policy, der Persistenz und der Cooldown-Lage."
        >
          <template #actions>
            <StatusPill
              :tone="alerting ? (alerting.outcome === 'send' ? 'ok' : alerting.outcome === 'failed' ? 'critical' : 'warn') : 'neutral'"
              :label="alerting?.outcome ?? 'Unknown'"
            />
          </template>

          <div v-if="alerting" class="kv-grid">
            <div>
              <span class="kv-label">Outcome</span>
              <span class="kv-value">{{ alerting.outcome }}</span>
            </div>
            <div>
              <span class="kv-label">Kind</span>
              <span class="kv-value">{{ alerting.alert_kind }}</span>
            </div>
            <div>
              <span class="kv-label">should_send</span>
              <span class="kv-value">{{ formatBoolean(alerting.should_send) }}</span>
            </div>
            <div>
              <span class="kv-label">sent</span>
              <span class="kv-value">{{ formatBoolean(alerting.sent) }}</span>
            </div>
            <div>
              <span class="kv-label">telegram_ready</span>
              <span class="kv-value">{{ formatBoolean(alerting.telegram_ready) }}</span>
            </div>
            <div>
              <span class="kv-label">Cooldown</span>
              <span class="kv-value">
                {{ alerting.cooldown_remaining_seconds !== null && alerting.cooldown_remaining_seconds !== undefined ? `${alerting.cooldown_remaining_seconds}s` : '—' }}
              </span>
            </div>
            <div>
              <span class="kv-label">Policy</span>
              <span class="kv-value">{{ alerting.policy_outcome }}</span>
            </div>
            <div>
              <span class="kv-label">Alert-Key</span>
              <span class="kv-value">{{ alerting.alert_key }}</span>
            </div>
          </div>

          <div class="section-copy">
            <p class="section-copy__summary">{{ alerting?.summary ?? 'Keine Alerting-Daten.' }}</p>
          </div>

          <div class="section-block">
            <h3 class="section-block__title">Telegram readiness</h3>
            <p class="section-copy__summary">
              {{ alerting?.telegram_ready_reason ?? '—' }}
            </p>
          </div>

          <div class="section-block">
            <h3 class="section-block__title">Reason-Codes</h3>
            <ReasonChips :items="alerting?.reason_codes ?? []" />
          </div>

          <div v-if="alerting?.send_result?.error" class="status-banner status-banner--warn">
            <strong>Telegram-Fehler:</strong> {{ alerting.send_result.error }}
          </div>
        </SectionCard>
      </section>
    </div>

    <section id="history" class="dashboard-section">
      <SectionCard
        title="Verlauf"
        eyebrow="Snapshots, Transitions, Alerts"
        subtitle="Die letzten gespeicherten Zustände, Wechsel und Alert-Entscheidungen in komprimierter Form."
      >
        <template #actions>
          <StatusPill :tone="latestTransition ? statusTone(latestTransition.to_status) : 'neutral'" :label="latestTransition ? `${statusLabel(latestTransition.from_status)} → ${statusLabel(latestTransition.to_status)}` : 'Kein Wechsel'" />
        </template>

        <div class="history-grid">
          <article class="history-column">
            <h3 class="section-block__title">Letzte Transitions</h3>
            <div v-if="recentTransitionItems.length > 0" class="history-list">
              <div v-for="item in recentTransitionItems" :key="item.id" class="history-item">
                <div class="history-item__head">
                  <StatusPill :tone="statusTone(item.to_status)" :label="`${statusLabel(item.from_status)} → ${statusLabel(item.to_status)}`" />
                  <span class="history-item__time">{{ formatTime(item.created_at) }}</span>
                </div>
                <p class="history-item__summary">{{ item.summary }}</p>
                <ReasonChips :items="item.reason_codes" />
              </div>
            </div>
            <p v-else class="empty-state">Noch keine Transitionen gespeichert.</p>
          </article>

          <article class="history-column">
            <h3 class="section-block__title">Letzte Snapshots</h3>
            <div v-if="recentSnapshotItems.length > 0" class="history-list">
              <div v-for="item in recentSnapshotItems" :key="item.id" class="history-item">
                <div class="history-item__head">
                  <StatusPill :tone="statusTone(item.guardian_status)" :label="statusLabel(item.guardian_status)" />
                  <span class="history-item__time">{{ formatTime(item.checked_at) }}</span>
                </div>
                <p class="history-item__summary">{{ item.overview_summary }}</p>
                <div class="history-item__meta">
                  <span>Router: {{ statusLabel(item.router_status) }}</span>
                  <span>System: {{ statusLabel(item.system_status) }}</span>
                  <span>auth: {{ formatBoolean(item.router_auth_required) }}</span>
                  <span>root: {{ formatBoolean(item.system_running_as_root) }}</span>
                </div>
                <ReasonChips :items="item.overview_reason_codes" />
              </div>
            </div>
            <p v-else class="empty-state">Noch keine Snapshots gespeichert.</p>
          </article>

          <article class="history-column">
            <h3 class="section-block__title">Letzte Alerts</h3>
            <div v-if="recentAlertItems.length > 0" class="history-list">
              <div v-for="item in recentAlertItems" :key="item.id" class="history-item">
                <div class="history-item__head">
                  <StatusPill :tone="alertTone(item.outcome)" :label="`${item.alert_kind} · ${item.outcome}`" />
                  <span class="history-item__time">{{ formatTime(item.checked_at) }}</span>
                </div>
                <p class="history-item__summary">{{ item.summary }}</p>
                <div class="history-item__meta">
                  <span>should_send: {{ formatBoolean(item.should_send) }}</span>
                  <span>sent: {{ formatBoolean(item.sent) }}</span>
                  <span>cooldown: {{ item.cooldown_remaining_seconds !== null && item.cooldown_remaining_seconds !== undefined ? `${item.cooldown_remaining_seconds}s` : '—' }}</span>
                </div>
                <ReasonChips :items="item.reason_codes" />
              </div>
            </div>
            <p v-else class="empty-state">Noch keine Alerts gespeichert.</p>
          </article>
        </div>
      </SectionCard>
    </section>

    <footer class="dashboard-footer">
      <div class="dashboard-footer__row">
        <span>Guardian backend: {{ current?.component ?? '—' }} v{{ current?.version ?? '—' }}</span>
        <span>History limit: {{ props.historyLimit }}</span>
        <span>Auto-refresh interval: {{ props.refreshIntervalMs }} ms</span>
      </div>
      <div class="dashboard-footer__row">
        <span>Latest snapshot: {{ latestSnapshot ? formatDateTime(latestSnapshot.checked_at) : '—' }}</span>
        <span>Latest alert: {{ latestAlert ? formatDateTime(latestAlert.checked_at) : '—' }}</span>
        <span>Latest transition: {{ latestTransition ? formatDateTime(latestTransition.created_at) : '—' }}</span>
      </div>
      <div class="dashboard-footer__row dashboard-footer__row--muted">
        <span>Guardian API target: {{ CONFIG.apiTarget }}</span>
        <span>Read only</span>
      </div>
    </footer>
  </div>
</template>
