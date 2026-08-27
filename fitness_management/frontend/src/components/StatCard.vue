<template>
  <div class="stat-card">
    <div class="stat-icon" :class="tone">{{ icon }}</div>
    <div>
      <div class="stat-card-value">{{ value }}<small>{{ unit }}</small></div>
      <div class="stat-card-label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: String,
  unit: String,
  icon: String,
  tone: String
});
</script>
