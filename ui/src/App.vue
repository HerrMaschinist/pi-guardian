<script setup lang="ts">
import { CONFIG } from './config';
import GuardianDashboardView from './components/GuardianDashboardView.vue';
</script>

<template>
  <GuardianDashboardView
    :api-base-path="CONFIG.apiBasePath"
    :history-limit="CONFIG.historyLimit"
    :refresh-interval-ms="CONFIG.refreshIntervalMs"
  />
</template>
