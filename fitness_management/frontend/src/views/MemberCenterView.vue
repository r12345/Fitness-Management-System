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
            <span class="user-avatar" style="width: 56px; height: 56px; font-size: 22px;">{{ profile.name }}</span>
            <div>
              <!-- 原来这里写死了 789，副标题也写死「会员编号 M1001 · 年卡」，
                   跟登录的会员没有半点关系 -->
              <h2 style="margin: 0;">{{ profile.name || '-' }}</h2>
              <div class="page-desc">会员编号 M{{ profile_info.id ?? '-' }} · {{ profile_info.card_type || '-' }}</div>
            </div>
          </div>
        </div>
        <div class="panel-body" style="border-top: 1px solid var(--border);">
          <div class="stat-grid" style="grid-template-columns: 1fr; margin-bottom: 0;">
            <div class="stat-card"><div><div class="stat-card-value">{{ profile_info.card_expire}}</div><div class="stat-card-label">到期时间</div></div></div>
            <div class="stat-card"><div><div class="stat-card-value">{{ profile_info.balance }}</div><div class="stat-card-label">账户余额</div></div></div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">近期安排</h2>
        </div>
        <div class="panel-body">
          <div v-for="item in myCourses" :key="item.id" class="course-card" style="margin-bottom: 12px;">
            <div class="course-card-top">
              <h3>{{ item.course.name }}</h3>
              <span class="badge" :class="item.tone">{{ item.status }}</span>
            </div>
            <div class="course-card-meta">
              <span>{{ formatTime(item.course.start_time) }}</span>
              <span v-if="item.schedule && item.schedule.location"> · {{ item.schedule.location }}</span>
            </div>
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
            <thead><tr><th>课程</th><th>上课时间</th><th>教练</th><th>地点</th><th>排课状态</th><th>预约状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="(item, index) in appointments" :key="index">
                <td>{{ courseNameOf(item) }}</td>
                <td>{{ classTimeOf(item) }}</td>
                <td>{{ coachNameOf(item) }}</td>
                <td>{{ item.schedule_location || '-' }}</td>
                <td><span class="badge" :class="scheduleStatusClass(item.schedule_status)">{{ item.schedule_status || '—' }}</span></td>
                <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
                <!-- 「待预约」是「已预约」的历史同义写法，只判断「已预约」会让老数据没有取消入口 -->
                <td><button v-if="isPendingStatus(item.status)" class="btn btn-danger btn-sm" type="button" @click="cancel(item)">取消预约</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'courses'" class="panel-body">
        <div class="course-cards">
          <div v-for="item in myCourses" :key="item.name" class="course-card">
            <div class="course-card-top"><h3>{{ item.course.name }}</h3><span class="badge info">{{ item.course.coach.name }}</span></div>
            <div class="course-card-meta">
              <span>{{ formatTime(item.course.start_time) }}</span>
              <!-- 上课地点随教练排课走：排课被教练改过地点，这里显示的就是最新那间教室 -->
              <span v-if="item.schedule && item.schedule.location"> · {{ item.schedule.location }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'booking'" class="panel-body no-padding">
        <!-- 会员可预约的排课：全部教练、当前时间起往后 4 周 -->
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>上课日期</th><th>星期</th><th>时间段</th><th>课程</th><th>教练</th><th>地点</th><th>已约/容量</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-if="!upcomingSchedules.length">
                <td colspan="9" style="text-align:center;color:#999;">暂无可预约的排课</td>
              </tr>
              <tr v-for="item in upcomingSchedules" :key="item.schedule_id">
                <td>{{ item.schedule_date }}</td>
                <td>{{ weekdayOf(item.schedule_date) }}</td>
                <td>{{ item.start_time }} ~ {{ item.end_time }}</td>
                <td>{{ item.course_name }}</td>
                <td>{{ item.coach_name || '-' }}</td>
                <td>{{ item.location || '-' }}</td>
                <td>{{ item.booked_count || 0 }}<template v-if="capacityOf(item)"> / {{ capacityOf(item) }}</template></td>
                <td><span class="badge" :class="scheduleStatusClass(item.status)">{{ item.status }}</span></td>
                <td>
                  <span v-if="item.booked_by_me" class="badge success">已预约</span>
                  <button v-else-if="item.can_book" class="btn btn-primary btn-sm" type="button" @click="bookSchedule(item)">预约</button>
                  <span v-else style="color:#999;">不可预约</span>
                </td>
              </tr>
            </tbody>
          </table>
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
                :class="queryPeriod === 'week' ? 'btn-primary' : 'btn-secondary'"
                type="button"
                @click="queryPeriod='week';fetchTrainingStat()"
              >本周</button>
              <button
                class="btn"
                :class="queryPeriod === 'month' ? 'btn-primary' : 'btn-secondary'"
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
          <button class="btn btn-primary" v-show="!checkinStore.checked_in" type="button" @click="member_checkIn">到店打卡</button>
          <button class="btn btn-primary" v-show="checkinStore.checked_in" type="button" @click="member_leave">离店打卡</button>
          <span v-if="checkinStore.checked_in" style="color: var(--muted); font-size: 13px;">
            当前已到店：{{ checkinStore.checkin_info.checkin_date }} {{ checkinStore.checkin_info.checkin_time }}
          </span>
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
              <button class="btn btn-secondary" type="button" @click="closeTrainDialog">取消</button>
              <button class="btn btn-primary" type="submit">提交保存</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref,onMounted } from "vue";
import { useToast } from "../composables/useToast";
import { confirmDialog } from "../composables/useConfirm.js";
import {getMyAppointments, getMyCourses, editProfile, get_member_info, getUpcomingSchedules} from "../api/member-center.js"
import {cancel_appointment, create_appointment} from "../api/appointments.js"
import {isPendingStatus, statusClass, scheduleStatusClass} from "../utils/appointmentStatus.js";
import TrendChart from "../components/TrendChart.vue";

import {
  create_checkin,
  leave_checkin,
  list_my_checkins,
  get_current_checkin,
  list_training_records,
  create_training_records,
  get_training_statistics
} from "../api/training.js";
import {useUserStore} from "../stores/user.js";
import {useCheckinStore} from '../stores/checkin.js'
const userStore = useUserStore()
const checkinStore = useCheckinStore()
const toast = useToast();
const activeTab = ref("appointments");
const tabs = [
  { key: "appointments", label: "我的预约" },
  { key: "booking", label: "可预约课程" },
  { key: "courses", label: "我的课程" },
  { key: "training", label: "训练记录" },
  { key: "checkin", label: "我的打卡" },
  { key: "profile", label: "个人信息" }
];
const upcoming = [
  { name: "哈他瑜伽", tag: "即将开始", tone: "warn", meta: "今天 19:30 - 20:30 · 刘洋" },
  { name: "一对一塑形", tag: "已预约", tone: "info", meta: "08月29日 15:00 · 张昊" }
];
const appointments = ref([]);
const myCourses = ref([])
const checkins = ref([]);
const profile = reactive({
  name: null,
  phone: null,
  height: null,
  weight: null
});

/** 卡片上要用的会员卡信息，跟 profile 分开存，避免和可编辑表单混在一起 */
const profile_info = ref({
  id: null,
  card_type: null,
  card_expire: null,
  balance: null
})

// 删掉旧的无效computed

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

const formatTime = (str) => {
  if (!str) return ''
  const d = new Date(str)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  const s = String(d.getSeconds()).padStart(2, '0')
  return `${y}年${m}月${day}日 ${h}:${mi}:${s}`
}

/**
 * 下列三个取值函数专门做「新旧返回体兼容」。
 *
 * 会员预约接口返回过两种形状：早期是 Appointment ORM（`course` 是嵌套对象 `{name, start_time, coach:{name}}`），
 * 现在是扁平字典（`course`/`coach` 是纯字符串，另带 schedule_* 排课字段）。
 * 前端若只认一种，一旦前后端版本错配（比如后端已更新、前端还是旧包），
 * 表格会整列空白——所以这里两种都兜住，不会因为一侧没更新就白屏。
 */
function courseNameOf(item) {
  if (!item) return '-'
  // 字符串直接用；旧形状取 course.name
  return typeof item.course === 'string' ? item.course : (item.course?.name ?? '-')
}

function coachNameOf(item) {
  if (!item) return '-'
  return item.coach ?? item.course?.coach?.name ?? '-'
}

/** 上课时间：优先用排课的日期+时段，其次预约时间，最后退回课程开始时间 */
function classTimeOf(item) {
  if (!item) return '-'
  if (item.schedule_date) {
    const start = item.schedule_start ?? ''
    const end = item.schedule_end ? `~${item.schedule_end}` : ''
    return `${item.schedule_date} ${start}${end}`.trim() || '-'
  }
  if (item.appointment_time) return formatTime(item.appointment_time)
  return item.course?.start_time ? formatTime(item.course.start_time) : '-'
}

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

async function member_info(){
  const res = await get_member_info()
  profile.name = res.data.name
  profile.phone = res.data.phone
  profile.height = res.data.height
  profile.weight = res.data.weight
  profile_info.value.id = res.data.id
  profile_info.value.card_type = res.data.card_type
  profile_info.value.card_expire = res.data.card_expire
  profile_info.value.balance = res.data.balance
}

async function saveProfile(){
  try {
    const res = await editProfile(profile)
    profile.height = res.data.height
    profile.weight = res.data.weight
    profile.phone = res.data.phone
    profile.name = res.data.name
    toast.show("修改成功")
  } catch (err) {
    toast.show(err.friendlyMessage || "修改失败", "error")
  }
}
async function get_Appointments(){
  const res = await getMyAppointments()
  appointments.value = res.data
}

/** 会员可预约的排课（全部教练、往后 4 周） */
const upcomingSchedules = ref([])

/** 团课看 max_count、私教看 capacity，和后端 can_book 的口径一致 */
function capacityOf(item) {
  return item.max_count || item.capacity || 0
}

/** 日期 → 星期几，会员看排课时比光看日期直观 */
function weekdayOf(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return '-'
  return '周' + '日一二三四五六'[d.getDay()]
}

async function get_upcoming_schedules() {
  try {
    const res = await getUpcomingSchedules()
    upcomingSchedules.value = res.data || []
  } catch (err) {
    toast.show(err.friendlyMessage || "加载可预约排课失败", "error")
  }
}

/** 预约某一次排课：带上排课的日期与开始时间，后端据此把它关联到这条排课上 */
async function bookSchedule(item) {
  try {
    await create_appointment({
      member_id: profile_info.value.id ?? 0,
      course_id: item.course_id,
      appointment_time: `${item.schedule_date} ${item.start_time}`
    })
    toast.show("预约成功")
    await Promise.all([get_upcoming_schedules(), get_Appointments()])
  } catch (err) {
    toast.show(err.friendlyMessage || "预约失败", "error")
  }
}

async function get_courses(){
  const res = await getMyCourses()
  myCourses.value = res.data
}


onMounted(async ()=>{
  await get_Appointments()
  await get_upcoming_schedules()
  await get_courses()
  await member_info()
})

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
    await create_training_records(trainRecordForm)
    toast.show("训练记录新增成功")
    closeTrainDialog()
    await getTrainingRecords() //刷新列表
  }catch(err){
    toast.show(err.friendlyMessage || "新增失败", "error")
  }
}

async function getTrainingRecords(){
  const res = await  list_training_records();
  trainRecords.value = res.data;
}

/** 用后端状态回填「到店 / 离店」按钮。
    刷新页面后光靠内存分不清有没有离店，必须以库里那条未离店的记录为准。 */
async function refreshCheckinState(){
  try {
    const res = await get_current_checkin();
    checkinStore.set_checkin_state(res.data);
  } catch (error) {
    console.error("获取在店状态失败", error);
  }
}

async function member_checkIn(){
  try{
    // 先取一个本地时间戳当作打卡时间
    checkinStore.checkin()
    await create_checkin(checkinStore.checkin_time);
    await memberCheckInList() // 列表刷新时会顺带把在店状态同步回来
    await fetchTrainingStat()
  }catch (error) {
    // 打卡失败要把本地时间戳回滚，否则按钮会错显示成「离店打卡」
    await refreshCheckinState()
    toast.show(error.friendlyMessage || "到店打卡失败", "error")
  }
}

async function member_leave(){
  // 离店打卡会结束本次到店记录并结算时长，属于「提交就不太好改」的操作，
  // 先用确认框报到店时间给用户核对一眼。
  const checkinTime = checkinStore.checkin_info?.checkin_time || "";
  const ok = await confirmDialog({
    title: "确认离店打卡",
    message: "离店后会结束本次到店记录，并据此结算本次训练时长。",
    details: checkinTime ? [{ label: "到店时间", value: String(checkinTime) }] : [],
    confirmText: "离店打卡"
  });
  if (!ok) return;
  try{
    checkinStore.leave()
    // checkin_id 来自后端返回的「当前在店」记录，刷新页面后依然拿得到
    await leave_checkin(checkinStore.checkin_info.checkin_id, checkinStore.leave_time);
    await memberCheckInList()
    // 这个接口 period 是必填，不传会 422；原来这里漏了参数
    await fetchTrainingStat()
  }catch (error) {
    await refreshCheckinState()
    toast.show(error.friendlyMessage || "离店打卡失败", "error")
  }
}

async function memberCheckInList(){
  const res = await list_my_checkins();
  checkins.value = res.data;
  // 顺带恢复「当前在店」状态：刷新页面后按钮不会被重置回「到店打卡」
  await refreshCheckinState()
}

onMounted(async ()=>{
  await memberCheckInList()
  await getTrainingRecords()
  await fetchTrainingStat() //初始化调用新函数
})

/**
 * 取消预约。
 * 原来只把数组里那条记录的 status 改成「已取消」，既没落库也没释放课程名额，
 * 刷新页面就复活了。
 */
async function cancel(item) {
  // 会员端取消自己的预约，确认框里带上课程与时间，避免点错行
  const ok = await confirmDialog({
    title: "取消预约",
    tone: "danger",
    message: "取消后席位会被释放，如需上课请重新预约。",
    details: [
      { label: "课程", value: courseNameOf(item) || "—" },
      { label: "时间", value: classTimeOf(item) || "—" },
      { label: "教练", value: coachNameOf(item) || "—" }
    ],
    confirmText: "取消预约"
  });
  if (!ok) return;
  try {
    await cancel_appointment(item.id)
    toast.show("预约已取消")
    await get_Appointments()
  } catch (err) {
    toast.show(err.friendlyMessage || "取消预约失败", "error")
  }
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