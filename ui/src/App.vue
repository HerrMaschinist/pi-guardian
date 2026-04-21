<script setup lang="ts">
import { CONFIG } from './config';
import GuardianDashboardView from './components/GuardianDashboardView.vue';
</script>

<template>
  <GuardianDashboardView
    :api-base-url="CONFIG.apiBaseUrl"
    :history-limit="CONFIG.historyLimit"
    :refresh-interval-ms="CONFIG.refreshIntervalMs"
  />
</template>
