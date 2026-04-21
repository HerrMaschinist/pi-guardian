<script setup lang="ts">
type Tone = 'ok' | 'warn' | 'critical' | 'info' | 'neutral';

interface Props {
  tone?: Tone;
  label: string;
}

withDefaults(defineProps<Props>(), {
  tone: 'neutral',
});
</script>

<template>
  <span :class="['status-pill', `status-pill--${tone}`]">
    <span class="status-pill__dot" />
    {{ label }}
  </span>
</template>
