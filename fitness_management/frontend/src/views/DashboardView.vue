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
          @click="period = item.value;get_one();get_four();"
        >
          {{ item.label }}
        </button>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard
        v-for="(item, index) in summaryData"
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
                <tr v-for="item in recent_appointments" :key="item.member + item.course">
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
                <tr v-for="(item, index) in log_list" :key="index">
                  <td>{{ item.operator }}</td>
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
import {computed, onMounted, ref} from "vue";
import { useAuth } from "../composables/useAuth";
import StatCard from "../components/StatCard.vue";
import TrendChart from "../components/TrendChart.vue";
import { get_dashboard_trend,get_dashboard_summary,get_card_distribution,get_recent_appointments } from "../api/dashboard.js";
import {get_recent_business_log,get_summary} from "../api/reception.js";
const auth = useAuth();
const period = ref("week");
const periods = [
  { label: "今日", value: "day" },
  { label: "本周", value: "week" },
  { label: "本月", value: "month" }
];

const log_list = ref([])
const recent_appointments = ref([])
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

const trendSeries = ref([
    {name: '会员数',data:[] ,area:true},
    {name: '总金额',data: [],area:true}
])
const summaryData = ref([
    { label: "会员总数", value: null, unit: "人", tone: "" },
    { label: "本期新增会员", value: null, unit: "人", tone: "" },
    { label: "过期会员", value: null, unit: "人", tone: "warn" },
    { label: "本期营收", value: null, unit: "元", tone: "" },
    { label: "课程预约量", value: null, unit: "次", tone: "danger" }
  ])
async function get_one(){
  const res = await get_dashboard_summary(period.value)
  summaryData.value[0]['value'] = res.data.total_members
  summaryData.value[1].value = res.data.new_members
  summaryData.value[2].value = res.data.expired_members
  summaryData.value[3].value = res.data.total_revenue
  summaryData.value[4].value = res.data.total_appointments
}

async function get_two(){
  const res = await get_recent_appointments()
  recent_appointments.value = res.data.items
}

async function get_three(){
  const res = await get_card_distribution()
  console.log(res)
}

async function get_four(){
  const res = await get_dashboard_trend(period.value)
  trendSeries.value[0]['data'] = res.data.members
  trendSeries.value[1]['data'] = res.data.revenue
}

async function get_log(){
  const res = await get_recent_business_log()
  log_list.value = res.data.items
}




onMounted(async() => {
  await get_one()
  await get_two()
  await get_three()
  await get_four()
  await get_log()
})

</script>
