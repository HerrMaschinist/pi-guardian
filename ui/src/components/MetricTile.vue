<script setup lang="ts">
interface Props {
  label: string;
  value: string;
  tone?: 'ok' | 'warn' | 'critical' | 'info' | 'neutral';
  hint?: string;
}

withDefaults(defineProps<Props>(), {
  tone: 'neutral',
});
</script>

<template>
  <article :class="['metric-tile', `metric-tile--${tone}`]">
    <span class="metric-tile__label">{{ label }}</span>
    <span class="metric-tile__value">{{ value }}</span>
    <span v-if="hint" class="metric-tile__hint">{{ hint }}</span>
  </article>
</template>
