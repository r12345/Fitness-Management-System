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
  // 统计值既可能是整数也可能是小数，只声明 String 会让 Vue 每次都报类型警告
  value: [String, Number],
  unit: String,
  icon: String,
  tone: String
});
</script>
