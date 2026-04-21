<script setup lang="ts">
interface Props {
  items: string[];
  emptyLabel?: string;
}

withDefaults(defineProps<Props>(), {
  emptyLabel: 'Keine Reason-Codes',
});
</script>

<template>
  <div class="reason-chips">
    <span v-if="items.length === 0" class="reason-chips__empty">{{ emptyLabel }}</span>
    <span v-for="item in items" :key="item" class="reason-chips__item">{{ item }}</span>
  </div>
</template>
