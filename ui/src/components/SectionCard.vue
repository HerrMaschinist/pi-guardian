<script setup lang="ts">
interface Props {
  title: string;
  eyebrow?: string;
  subtitle?: string;
}

defineProps<Props>();
</script>

<template>
  <section class="section-card">
    <header class="section-card__header">
      <div class="section-card__titles">
        <span v-if="eyebrow" class="section-card__eyebrow">{{ eyebrow }}</span>
        <h2 class="section-card__title">{{ title }}</h2>
        <p v-if="subtitle" class="section-card__subtitle">{{ subtitle }}</p>
      </div>
      <div class="section-card__actions">
        <slot name="actions" />
      </div>
    </header>
    <div class="section-card__body">
      <slot />
    </div>
  </section>
</template>
