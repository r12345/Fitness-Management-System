<template>
  <router-view />
  <!-- 全局确认弹窗：挂在根组件上，各页面用 confirmDialog() 触发，样式统一 -->
  <ConfirmDialog />
</template>

<script setup>
// 根组件只负责承载路由视图 + 全局弹窗
import ConfirmDialog from "./components/ConfirmDialog.vue";
</script>
