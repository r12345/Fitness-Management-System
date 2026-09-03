<template>
  <div>
    <transition name="fade">
      <div v-if="toast.message" class="toast-banner" :class="toast.type">{{ toast.message }}</div>
    </transition>

    <div class="page-header">
      <div>
        <h1>会员个人中心</h1>
        <p class="page-desc">查看预约、课程、训练记录、打卡和个人信息。</p>
      </div>
    </div>

    <div class="split-layout" style="margin-bottom: 20px;">
      <div class="panel">
        <div class="panel-body">
          <div class="page-actions">
            <span class="user-avatar" style="width: 56px; height: 56px; font-size: 22px;">{{ shortName }}</span>
            <div>
              <h2 style="margin: 0;">{{ member_info.name }}</h2>
              <div class="page-desc">会员编号 M1001 · 年卡</div>
            </div>
          </div>
        </div>
        <div class="panel-body" style="border-top: 1px solid var(--border);">
          <div class="stat-grid" style="grid-template-columns: 1fr; margin-bottom: 0;">
            <div class="stat-card"><div><div class="stat-card-value">{{ member_info.card_expire}}</div><div class="stat-card-label">到期时间</div></div></div>
            <div class="stat-card"><div><div class="stat-card-value">{{ member_info.balance }}</div><div class="stat-card-label">账户余额</div></div></div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">近期安排</h2>
        </div>
        <div class="panel-body">
          <div v-for="item in upcoming" :key="item.name" class="course-card" style="margin-bottom: 12px;">
            <div class="course-card-top">
              <h3>{{ item.name }}</h3>
              <span class="badge" :class="item.tone">{{ item.tag }}</span>
            </div>
            <div class="course-card-meta"><span>{{ item.meta }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          type="button"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <div v-if="activeTab === 'appointments'" class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>课程</th><th>上课时间</th><th>教练</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="(item, index) in appointments" :key="index">
                <td>{{ item.course }}</td><td>{{ item.time }}</td><td>{{ item.coach }}</td>
                <td><span class="badge" :class="item.status === '已完成' ? 'success' : item.status === '已取消' ? 'muted' : 'info'">{{ item.status }}</span></td>
                <td><button v-if="item.status === '已预约'" class="btn btn-danger btn-sm" type="button" @click="cancel(index)">取消预约</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'courses'" class="panel-body">
        <div class="course-cards">
          <div v-for="item in myCourses" :key="item.name" class="course-card">
            <div class="course-card-top"><h3>{{ item.name }}</h3><span class="badge info">{{ item.tag }}</span></div>
            <div class="course-card-meta"><span>{{ item.meta }}</span></div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'training'" class="panel-body">
        <div class="panel">
          <div class="panel-header"><h2 class="panel-title">本月训练频率</h2></div>
          <div class="panel-body no-padding">
            <TrendChart :categories="['第1周','第2周','第3周','第4周']" :series="trainingSeries" />
          </div>
        </div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>日期</th><th>训练内容</th><th>重量</th><th>时长</th><th>体脂率</th></tr></thead>
            <tbody>
              <tr v-for="(item, index) in trainingRecords" :key="index">
                <td>{{ item.date }}</td><td>{{ item.content }}</td><td>{{ item.weight }}</td><td>{{ item.duration }}</td><td>{{ item.fat }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'checkin'" class="panel-body">
        <div class="page-actions" style="margin-bottom: 16px;">
          <button class="btn btn-primary" type="button" @click="checkin">到店打卡</button>
        </div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>打卡日期</th><th>到店时间</th><th>离开时间</th><th>训练时长</th></tr></thead>
            <tbody>
              <tr v-for="(item, index) in checkins" :key="index">
                <td>{{ item.date }}</td><td>{{ item.in }}</td><td>{{ item.out }}</td><td>{{ item.duration }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else class="panel-body">
        <form class="form-grid" style="max-width: 760px;" @submit.prevent="saveProfile">
          <div class="field"><label>姓名</label><input v-model="profile.name" type="text"></div>
          <div class="field"><label>手机号</label><input v-model="profile.phone" type="text"></div>
          <div class="field"><label>身高（厘米）</label><input v-model.number="profile.height" type="number"></div>
          <div class="field"><label>体重（千克）</label><input v-model.number="profile.weight" type="number"></div>
          <div class="field full"><button class="btn btn-primary" type="submit">保存修改</button></div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useToast } from "../composables/useToast";
import { memberAppointments, trainingRecords } from "../data/mock";
import TrendChart from "../components/TrendChart.vue";
// import {getMemberById } from "../api/member_center.js";
import { onMounted} from  "vue";
const member_info = ref({

});
// const auth = useAuth();
const toast = useToast();
const userName =  "王琳";
const activeTab = ref("appointments");
const tabs = [
  { key: "appointments", label: "我的预约" },
  { key: "courses", label: "我的课程" },
  { key: "training", label: "训练记录" },
  { key: "checkin", label: "我的打卡" },
  { key: "profile", label: "个人信息" }
];
const upcoming = [
  { name: "哈他瑜伽", tag: "即将开始", tone: "warn", meta: "今天 19:30 - 20:30 · 刘洋" },
  { name: "一对一塑形", tag: "已预约", tone: "info", meta: "08月29日 15:00 · 张昊" }
];
const appointments = ref(memberAppointments.map((item) => ({ ...item })));
const myCourses = [
  { name: "哈他瑜伽", tag: "已预约", meta: "周一 19:30 · 刘洋" },
  { name: "一对一塑形", tag: "已预约", meta: "私教课 · 张昊" },
  { name: "燃脂有氧操", tag: "已完成", meta: "周三 18:00 · 孙悦" }
];
const checkins = ref([
  { date: "2026-08-26", in: "18:42", out: "20:05", duration: "83 分钟" },
  { date: "2026-08-24", in: "19:10", out: "20:40", duration: "90 分钟" }
]);
const profile = reactive({
  name: userName,
  phone: "13800000001",
  height: 168,
  weight: 56.4
});
const trainingSeries = computed(() => [
  { name: "训练次数", data: [2, 3, 4, 3], area: true }
]);
const shortName = computed(() => {
  const name = member_info.value?.name
  return name ? name.slice(0,2) : ''
})



onMounted(async ()=>{
  const res = await getMemberById();
  member_info.value = res.data;
  console.log(res.data)
})

function cancel(index) {
  appointments.value[index].status = "已取消";
  toast.show("预约已取消");
}

function checkin() {
  const now = new Date();
  checkins.value.unshift({
    date: now.toISOString().slice(0, 10),
    in: now.toTimeString().slice(0, 5),
    out: "待记录",
    duration: "训练中"
  });
  toast.show("到店打卡成功");
}

function saveProfile() {
  toast.show("个人信息已保存");
}
</script>
