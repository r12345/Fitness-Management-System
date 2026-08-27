<template>
  <div>
    <div class="page-header">
      <div>
        <h1>{{ pageTitle }}</h1>
        <p class="page-desc">{{ pageDesc }}</p>
      </div>
      <div class="page-actions">
        <button
          v-for="item in periods"
          :key="item.value"
          class="btn btn-secondary btn-sm"
          :class="{ 'btn-primary': period === item.value }"
          type="button"
          @click="period = item.value"
        >
          {{ item.label }}
        </button>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard
        v-for="(item, index) in dashboardData.stats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :unit="item.unit"
        :tone="item.tone"
        :icon="['人', '增', '过', '收', '约'][index]"
      />
    </div>

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">会员与营收趋势</h2>
      </div>
      <div class="panel-body no-padding">
        <TrendChart :categories="trendCategories" :series="trendSeries" />
      </div>
    </div>

    <div class="split-layout">
      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">近期预约</h2>
        </div>
        <div class="panel-body no-padding">
          <div class="data-table-wrap">
            <table class="data-table">
              <thead>
                <tr><th>会员</th><th>课程</th><th>时间</th><th>状态</th></tr>
              </thead>
              <tbody>
                <tr v-for="item in dashboardData.recentReservations" :key="item.member + item.course">
                  <td>{{ item.member }}</td>
                  <td>{{ item.course }}</td>
                  <td>{{ item.time }}</td>
                  <td><span class="badge" :class="item.status === '已签到' ? 'success' : 'info'">{{ item.status }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">关键操作日志</h2>
        </div>
        <div class="panel-body no-padding">
          <div class="data-table-wrap">
            <table class="data-table">
              <thead>
                <tr><th>操作人</th><th>操作内容</th><th>时间</th></tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in dashboardData.activity" :key="index">
                  <td>{{ item.user }}</td>
                  <td>{{ item.content }}</td>
                  <td>{{ item.time }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useAuth } from "../composables/useAuth";
import { dashboardData } from "../data/mock";
import StatCard from "../components/StatCard.vue";
import TrendChart from "../components/TrendChart.vue";

const auth = useAuth();
const period = ref("week");
const periods = [
  { label: "今日", value: "day" },
  { label: "本周", value: "week" },
  { label: "本月", value: "month" }
];

const pageTitle = computed(() => auth.currentRole.value === "reception" ? "运营概览" : "数据大盘");
const pageDesc = computed(() => auth.currentRole.value === "reception"
  ? "查看今日开卡、预约、消费和报修动态。"
  : "查看场馆核心运营指标与近期业务动态。");

const trendCategories = computed(() => {
  if (period.value === "day") {
    return ["09:00", "11:00", "14:00", "16:00", "18:00", "20:00"];
  }
  if (period.value === "month") {
    return ["第1周", "第2周", "第3周", "第4周", "第5周"];
  }
  return ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
});

const trendSeries = computed(() => {
  if (period.value === "day") {
    return [
      { name: "会员数", data: [8, 16, 22, 26, 31, 18], area: true },
      { name: "营收", data: [1200, 2600, 5200, 6800, 8600, 4200], area: true }
    ];
  }
  if (period.value === "month") {
    return [
      { name: "会员数", data: [86, 108, 96, 124, 42], area: true },
      { name: "营收", data: [16800, 21400, 19800, 25600, 8200], area: true }
    ];
  }
  return [
    { name: "会员数", data: [18, 26, 21, 34, 29, 42, 23], area: true },
    { name: "营收", data: [3200, 5600, 4200, 8900, 7600, 12400, 6800], area: true }
  ];
});
</script>
