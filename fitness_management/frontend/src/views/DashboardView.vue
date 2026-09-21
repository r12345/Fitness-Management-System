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
          @click="period = item.value; get_one(); get_four();"
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

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">会员卡种分布</h2>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table" style="min-width: 0;">
            <thead>
              <tr><th>卡种</th><th>在册正常会员</th></tr>
            </thead>
            <tbody>
              <tr v-if="!cardDistribution.length">
                <td colspan="2" style="text-align:center;color:#999;">暂无数据</td>
              </tr>
              <tr v-for="item in cardDistribution" :key="item.card_type">
                <td>{{ item.card_type || '未填写' }}</td>
                <td>{{ item.count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
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
                <tr v-if="!recent_appointments.length">
                  <td colspan="4" style="text-align:center;color:#999;">近三天暂无预约</td>
                </tr>
                <tr v-for="item in recent_appointments" :key="item.member + item.course + item.time">
                  <td>{{ item.member }}</td>
                  <td>{{ item.course }}</td>
                  <td>{{ item.time }}</td>
                  <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
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
                <tr v-if="!log_list.length">
                  <td colspan="3" style="text-align:center;color:#999;">今日暂无业务动态</td>
                </tr>
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
import { computed, onMounted, ref } from "vue";
import { useAuth } from "../composables/useAuth";
import StatCard from "../components/StatCard.vue";
import TrendChart from "../components/TrendChart.vue";
import { get_dashboard_trend, get_dashboard_summary, get_card_distribution, get_recent_appointments } from "../api/dashboard.js";
import { get_recent_business_log } from "../api/reception.js";
import { statusClass } from "../utils/appointmentStatus.js";

const auth = useAuth();
const period = ref("week");
const periods = [
  { label: "今日", value: "day" },
  { label: "本周", value: "week" },
  { label: "本月", value: "month" }
];

const log_list = ref([])
const recent_appointments = ref([])
const cardDistribution = ref([])
const pageTitle = computed(() => auth.currentRole.value === "reception" ? "运营概览" : "数据大盘");
const pageDesc = computed(() => auth.currentRole.value === "reception"
  ? "查看今日开卡、预约、消费和报修动态。"
  : "查看场馆核心运营指标与近期业务动态。");

// x 轴直接用后端返回的 categories：后端按周期生成连续标签
// （本周周一到周日 / 本月每天 / 今日只有一天）。
// 原来是前端硬编码一套标签，和后端实际返回的数据点数量可能对不上，图会画歪。
const trendCategories = ref([]);

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
  try {
    const res = await get_dashboard_summary(period.value)
    summaryData.value[0]['value'] = res.data.total_members
    summaryData.value[1].value = res.data.new_members
    summaryData.value[2].value = res.data.expired_members
    summaryData.value[3].value = res.data.total_revenue
    summaryData.value[4].value = res.data.total_appointments
  } catch (err) {
    // 概览拉不到时保持占位，不要把整页搞白
  }
}

async function get_two(){
  const res = await get_recent_appointments()
  recent_appointments.value = res.data.items
}

async function get_three(){
  const res = await get_card_distribution()
  cardDistribution.value = res.data.items || []
}

async function get_four(){
  const res = await get_dashboard_trend(period.value)
  trendCategories.value = res.data.categories || []
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
