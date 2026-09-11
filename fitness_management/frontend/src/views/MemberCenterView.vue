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
              <h2 style="margin: 0;">789</h2>
              <div class="page-desc">会员编号 M1001 · 年卡</div>
            </div>
          </div>
        </div>
        <div class="panel-body" style="border-top: 1px solid var(--border);">
          <div class="stat-grid" style="grid-template-columns: 1fr; margin-bottom: 0;">
            <div class="stat-card"><div><div class="stat-card-value">456</div><div class="stat-card-label">到期时间</div></div></div>
            <div class="stat-card"><div><div class="stat-card-value">123</div><div class="stat-card-label">账户余额</div></div></div>
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
          <div class="panel-header" style="display:flex;align-items:center;justify-content:space-between;">
            <h2 class="panel-title">训练统计</h2>
            <!--原生按钮组，和页面btn样式统一，不需要element -->
            <div class="btn-group">
              <button
                class="btn"
                :class="queryPeriod === 'week' ? 'btn-primary' : 'btn-default'"
                type="button"
                @click="queryPeriod='week';fetchTrainingStat()"
              >本周</button>
              <button
                class="btn"
                :class="queryPeriod === 'month' ? 'btn-primary' : 'btn-default'"
                type="button"
                @click="queryPeriod='month';fetchTrainingStat()"
              >本月</button>
            </div>
          </div>

          <!--统计行，和页面风格统一，不要硬写死flex gap，用stat‑card风格 -->
          <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;gap:40px;">
            <div>
              <div class="stat-card-label">统计周期</div>
              <div class="stat-card-value">{{ queryPeriod === 'month' ? '本月' : '本周' }}</div>
            </div>
            <div>
              <div class="stat-card-label">总训练次数</div>
              <div class="stat-card-value">{{ statData.training_count }} 次</div>
            </div>
            <div>
              <div class="stat-card-label">总训练时长</div>
              <div class="stat-card-value">{{ statData.training_minutes }} 分钟</div>
            </div>
          </div>

          <div class="panel-body no-padding">
            <TrendChart :categories="categories" :series="trainingSeries" />
          </div>
        </div>

        <button class="btn btn-primary" type="button" @click="openTrainDialog">新增训练记录</button>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>日期</th><th>训练内容</th><th>重量</th><th>时长</th><th>体脂率</th></tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in trainRecords" :key="index">
                <td>{{ item.train_date }}</td>
                <td>{{ item.content }}</td>
                <td>{{ item.weight }}kg</td>
                <td>{{ item.duration_minutes }}分钟</td>
                <td>{{ item.fat_rate }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'checkin'" class="panel-body">
        <div class="page-actions" style="margin-bottom: 16px;">
          <button class="btn btn-primary" v-show="!checkinStore.checkin_time" type="button" @click="member_checkIn">到店打卡</button>
          <button class="btn btn-primary" v-show="checkinStore.checkin_time" type="button" @click="member_leave">离店打卡</button>
        </div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>打卡日期</th><th>到店时间</th><th>离开时间</th><th>训练时长</th></tr></thead>
            <tbody>
            <tr v-for="(item, index) in checkins" :key="index">
              <td>{{ item.checkin_date }}</td>
              <td>{{ item.checkin_time }}</td>
              <td>{{ item.leave_time }}</td>
              <td>{{ item.duration }}</td>
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

    <!-- ==========新增训练记录弹窗========== -->
    <div v-if="showTrainDialog" class="dialog-mask" @click.self="closeTrainDialog">
      <div class="dialog">
        <div class="dialog-header">
          <h3>新增训练记录</h3>
          <button class="dialog-close" @click="closeTrainDialog">×</button>
        </div>
        <div class="dialog-body">
          <form class="form-grid" @submit.prevent="submitTrainRecord">
            <div class="field">
              <label>训练日期</label>
              <input v-model="trainRecordForm.train_date" type="date" required />
            </div>
            <div class="field">
              <label>训练内容</label>
              <input v-model="trainRecordForm.content" type="text" placeholder="例如：肩背力量训练" required />
            </div>
            <div class="field">
              <label>训练重量(kg)</label>
              <input v-model="trainRecordForm.weight" type="text"  />
            </div>
            <div class="field">
              <label>训练时长(分钟)</label>
              <input v-model.number="trainRecordForm.duration_minutes" type="number" />
            </div>
            <div class="field">
              <label>体脂率(%)</label>
              <input v-model.number="trainRecordForm.fat_rate" type="number" step="0.1" />
            </div>
            <div class="field">
              <label>当前体重(kg)</label>
              <input v-model.number="trainRecordForm.body_weight" type="number" step="0.1" />
            </div>
            <div class="field full" style="display:flex;gap:12px;margin-top:12px;">
              <button class="btn btn-default" type="button" @click="closeTrainDialog">取消</button>
              <button class="btn btn-primary" type="submit">提交保存</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useToast } from "../composables/useToast";
import { memberAppointments, trainingRecords } from "../data/mock";
import TrendChart from "../components/TrendChart.vue";

import { onMounted} from  "vue";
import {
  create_checkin,
  leave_checkin,
  list_my_checkins,
  list_training_records,
  create_training_records,
  get_training_statistics
} from "../api/training.js";
import {useUserStore} from "../stores/user.js";
import {useCheckinStore} from '../stores/checkin.js'
const userStore = useUserStore()
const checkinStore = useCheckinStore()
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
const checkins = ref([]);
const profile = reactive({
  name: userName,
  phone: "13800000001",
  height: 168,
  weight: 56.4
});

// 删掉旧的无效computed
const shortName = computed(() => {
  return userStore.role_name
})
const trainRecords = ref([]);

const categories = ref([])
const trainingSeries = ref([])
const queryPeriod = ref('month')

const statData = ref({
  period: '',
  training_count: 0,
  training_minutes: 0,
  trend: {
    categories: [],
    data: []
  }
})

// ✅ 切换周期调用这个函数，把queryPeriod传给接口
async function fetchTrainingStat(){
  const res = await get_training_statistics(queryPeriod.value)
  statData.value = res.data
  categories.value = statData.value.trend.categories
  trainingSeries.value = [
    {
      name: '训练次数',
      data: statData.value.trend.data,
      area: true
    }
  ]
}

//弹窗开关
const showTrainDialog = ref(false)

const trainRecordForm = reactive({
  member_id:null,
  train_date: '',
  content:'',
  weight: 0,
  duration_minutes: 0,
  fat_rate: 0,
  body_weight:0
})

//打开弹窗
function openTrainDialog(){
  //赋值会员id，从userStore拿
  trainRecordForm.member_id = userStore.role_id
  //清空旧表单
  trainRecordForm.train_date = ''
  trainRecordForm.content = ''
  trainRecordForm.weight = 0
  trainRecordForm.duration_minutes = 0
  trainRecordForm.fat_rate = 0
  trainRecordForm.body_weight = 0
  showTrainDialog.value = true
}
//关闭弹窗
function closeTrainDialog(){
  showTrainDialog.value = false
}
//提交表单
async function submitTrainRecord(){
  try {
    console.log(trainRecordForm)
    await create_training_records(trainRecordForm)
    toast.show("训练记录新增成功")
    closeTrainDialog()
    await getTrainingRecords() //刷新列表
  }catch(err){
    console.error(err)
    toast.show("新增失败","error")
  }
}

async function getTrainingRecords(){
  const res = await  list_training_records();
  console.log(res.data)
  trainRecords.value = res.data;
}

async function member_checkIn(){
  try{
    checkinStore.checkin()
    const res = await create_checkin(checkinStore.checkin_time);
    console.log(res.data)
    checkinStore.get_checkin_info(res.data)
    await memberCheckInList()
  }catch (error) {
    console.log(error)
  }
}

async function member_leave(){
  try{
    checkinStore.leave()
    console.log(checkinStore.checkin_info.checkin_id,checkinStore.leave_time)
    const res = await leave_checkin(checkinStore.checkin_info.checkin_id,checkinStore.leave_time);
    console.log(res)
    await memberCheckInList()
  }catch (error) {
    console.log(error)
  }
}

async function memberCheckInList(){
  const res = await list_my_checkins();
  checkins.value = res.data;
  console.log(res)
}

onMounted(async ()=>{
  await memberCheckInList()
  await getTrainingRecords()
  await fetchTrainingStat() //初始化调用新函数
})

function cancel(index) {
  appointments.value[index].status = "已取消";
  toast.show("预约已取消");
}

function saveProfile() {
  toast.show("个人信息已保存");
}
</script>

<style scoped>
.dialog-mask{
  position: fixed;
  inset:0;
  background:rgba(0,0,0,0.45);
  display:flex;
  align-items:center;
  justify-content:center;
  z-index:999;
}
.dialog{
  width:520px;
  background:#fff;
  border-radius:8px;
  overflow:hidden;
}
.dialog-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:14px 18px;
  border-bottom:1px solid var(--border);
}
.dialog-close{
  border:none;
  background:none;
  font-size:22px;
  cursor:pointer;
  padding:0 6px;
}
.dialog-body{
  padding:18px;
}
.form-grid{
  display:grid;
  gap:14px;
}
.field{
  display:flex;
  flex-direction:column;
  gap:4px;
}
.field.full{
  grid-column:1/-1;
}
/* 按钮组间距，和页面风格融合 */
.btn-group > .btn{
  margin-left:4px;
}
</style>