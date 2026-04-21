import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

import { fetchGuardianHistory, fetchGuardianStatus } from '../api/client';
import type { GuardianHistoryResponse, GuardianStatusResponse } from '../types';

interface UseGuardianDashboardOptions {
  apiBaseUrl: string;
  historyLimit: number;
  refreshIntervalMs: number;
}

export function useGuardianDashboard(options: UseGuardianDashboardOptions) {
  const status = ref<GuardianStatusResponse | null>(null);
  const history = ref<GuardianHistoryResponse | null>(null);
  const loading = ref(true);
  const refreshing = ref(false);
  const statusError = ref<string | null>(null);
  const historyError = ref<string | null>(null);
  const lastUpdatedAt = ref<string | null>(null);
  const autoRefreshEnabled = ref(true);
  const refreshInterval = ref<number | null>(null);

  const hasData = computed(() => Boolean(status.value || history.value));
  const errorMessage = computed(() => {
    const messages = [statusError.value, historyError.value].filter(Boolean);
    return messages.length > 0 ? messages.join(' · ') : null;
  });

  async function refresh() {
    refreshing.value = true;
    statusError.value = null;
    historyError.value = null;

    const [statusResult, historyResult] = await Promise.allSettled([
      fetchGuardianStatus(options.apiBaseUrl),
      fetchGuardianHistory(options.historyLimit, options.apiBaseUrl),
    ]);

    if (statusResult.status === 'fulfilled') {
      status.value = statusResult.value;
      lastUpdatedAt.value = statusResult.value.checked_at;
    } else {
      statusError.value = statusResult.reason instanceof Error ? statusResult.reason.message : 'Guardian-Status konnte nicht geladen werden.';
    }

    if (historyResult.status === 'fulfilled') {
      history.value = historyResult.value;
    } else {
      historyError.value = historyResult.reason instanceof Error ? historyResult.reason.message : 'Verlauf konnte nicht geladen werden.';
    }

    loading.value = false;
    refreshing.value = false;
  }

  function startAutoRefresh() {
    stopAutoRefresh();
    if (!autoRefreshEnabled.value || options.refreshIntervalMs <= 0) {
      refreshInterval.value = null;
      return;
    }
    refreshInterval.value = window.setInterval(() => {
      void refresh();
    }, options.refreshIntervalMs);
  }

  function stopAutoRefresh() {
    if (refreshInterval.value !== null) {
      window.clearInterval(refreshInterval.value);
      refreshInterval.value = null;
    }
  }

  function setAutoRefreshEnabled(enabled: boolean) {
    autoRefreshEnabled.value = enabled;
    startAutoRefresh();
  }

  onMounted(async () => {
    await refresh();
    startAutoRefresh();
  });

  onBeforeUnmount(() => {
    stopAutoRefresh();
  });

  return {
    status,
    history,
    loading,
    refreshing,
    errorMessage,
    statusError,
    historyError,
    hasData,
    lastUpdatedAt,
    autoRefreshEnabled,
    refresh,
    setAutoRefreshEnabled,
  };
}
