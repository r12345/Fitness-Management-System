<template>
  <div ref="chartEl" class="trend-chart"></div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";

const props = defineProps({
  categories: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] }
});

const chartEl = ref(null);
let chart = null;

function render() {
  if (!chartEl.value) {
    return;
  }
  if (!chart) {
    chart = echarts.init(chartEl.value);
  }
  chart.setOption({
    color: ["#0f766e", "#d97706", "#2563eb"],
    tooltip: { trigger: "axis" },
    legend: { top: 8, right: 12 },
    grid: { left: 44, right: 36, top: 48, bottom: 32 },
    xAxis: {
      type: "category",
      data: props.categories,
      boundaryGap: false
    },
    yAxis: { type: "value" },
    series: props.series.map(function (item) {
      return {
        name: item.name,
        type: item.type || "line",
        smooth: true,
        data: item.data,
        areaStyle: item.area ? { opacity: item.opacity || 0.12 } : undefined
      };
    })
  });
}

function handleResize() {
  if (chart) {
    chart.resize();
  }
}

watch(
  () => [props.categories, props.series],
  function () {
    nextTick(render);
  },
  { deep: true }
);

onMounted(function () {
  nextTick(render);
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(function () {
  window.removeEventListener("resize", handleResize);
  if (chart) {
    chart.dispose();
  }
});
</script>

<style scoped>
.trend-chart {
  width: 100%;
  height: 320px;
}
</style>
