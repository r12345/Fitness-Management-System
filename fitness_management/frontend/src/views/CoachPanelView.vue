<template>
  <div>
    <transition name="fade">
      <div v-if="toast.message" class="toast-banner" :class="toast.type">{{ toast.message }}</div>
    </transition>

    <div class="page-header">
      <div>
        <h1>教练工作台</h1>
        <p class="page-desc">查看排课、学员、授课记录并制定训练计划。</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary" type="button" @click="openSchedule">新增排课</button>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard label="本月排课" value="18" unit="节" icon="排" />
      <StatCard label="已授课时" value="42" unit="课时" icon="课" />
      <StatCard label="我的学员" value="16" unit="人" icon="学" />
      <StatCard label="平均评分" value="4.9" unit="分" icon="分" />
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

      <div v-if="activeTab === 'schedule'" class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>日期</th><th>时段</th><th>课程</th><th>地点</th><th>预约人数</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-if="!schedules.length"><td colspan="7" style="text-align:center;color:#999;">暂无排课</td></tr>
              <tr v-for="(item, index) in schedules" :key="item.id">
                <td>{{ item.schedule_date }}</td>
                <td>{{ item.start_time }} ~ {{ item.end_time }}</td>
                <td>{{ item.course_name }}</td>
                <td>{{ item.location }}</td>
                <td>{{ item.booked_count }} 人</td>
                <td><span class="badge" :class="item.status === '已签到' ? 'success' : item.status === '未开始' ? 'info' : 'warn'">{{ item.status }}</span></td>
                <td><button class="btn btn-secondary btn-sm" type="button" @click="checkSchedule(index)">签到确认</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'students'" class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>学员</th><th>手机号</th><th>训练目标</th><th>当前计划</th><th>最近训练</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="item in students" :key="item.name">
                <td>{{ item.name }}</td><td>{{ item.phone }}</td><td>{{ item.goal }}</td><td>{{ item.plan }}</td><td>{{ item.recent }}</td>
                <td><button class="btn btn-secondary btn-sm" type="button" @click="openPlan(item)">制定计划</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'records'" class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>日期</th><th>课程</th><th>学员</th><th>课时</th><th>评分</th><th>评价</th></tr></thead>
            <tbody>
              <tr v-for="(item, index) in records" :key="index">
                <td>{{ item.date }}</td><td>{{ item.course }}</td><td>{{ item.student }}</td><td>{{ item.hours }}</td><td>{{ item.score }}</td><td>{{ item.comment }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else class="panel-body">
        <div class="page-actions" style="margin-bottom: 16px;">
          <button class="btn btn-primary" type="button" @click="openPlan(null)">新增训练计划</button>
        </div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>学员</th><th>训练目标</th><th>主要部位</th><th>动作内容</th><th>组数次数</th><th>频率</th></tr></thead>
            <tbody>
              <tr v-for="(item, index) in plans" :key="index">
                <td>{{ item.student }}</td><td>{{ item.goal }}</td><td>{{ item.part }}</td><td>{{ item.action }}</td><td>{{ item.sets }}</td><td>{{ item.frequency }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="showSchedule" class="modal-mask" @click.self="showSchedule = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">新增排课</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showSchedule = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field">
              <label>课程</label>
              <select v-model="scheduleForm.course_id">
                <option :value="null" disabled>请选择课程</option>
                <option v-for="c in courseOptions" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="field"><label>日期</label><input v-model="scheduleForm.schedule_date" type="date"></div>
            <div class="field"><label>开始时间</label><input v-model="scheduleForm.start_time" type="time"></div>
            <div class="field"><label>结束时间</label><input v-model="scheduleForm.end_time" type="time"></div>
            <div class="field"><label>地点</label><input v-model="scheduleForm.location" type="text"></div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showSchedule = false">取消</button>
          <button class="btn btn-primary" type="button" @click="saveSchedule">保存排课</button>
        </div>
      </div>
    </div>

    <div v-if="showPlan" class="modal-mask" @click.self="showPlan = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">制定训练计划</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showPlan = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field"><label>学员</label><input v-model="planForm.student" type="text"></div>
            <div class="field"><label>训练目标</label><input v-model="planForm.goal" type="text"></div>
            <div class="field"><label>主要部位</label><input v-model="planForm.part" type="text"></div>
            <div class="field"><label>动作内容</label><input v-model="planForm.action" type="text"></div>
            <div class="field"><label>组数次数</label><input v-model="planForm.sets" type="text"></div>
            <div class="field"><label>频率</label><input v-model="planForm.frequency" type="text"></div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showPlan = false">取消</button>
          <button class="btn btn-primary" type="button" @click="savePlan">保存计划</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from "vue";
import { useToast } from "../composables/useToast";
import { coachPlans, coachStudents } from "../data/mock";
import { getSchedules, addSchedule } from "../api/coach";
import { list_courses } from "../api/courses";
import StatCard from "../components/StatCard.vue";

const toast = useToast();
const activeTab = ref("schedule");
const tabs = [
  { key: "schedule", label: "我的排课" },
  { key: "students", label: "我的学员" },
  { key: "records", label: "授课记录" },
  { key: "plans", label: "训练计划" }
];
const schedules = ref([]);
const courseOptions = ref([]);
const students = ref(coachStudents.map((item) => ({ ...item })));
const records = [
  { date: "2026-08-26", course: "增肌基础课", student: "王琳", hours: "1 课时", score: "5.0", comment: "动作执行标准" },
  { date: "2026-08-25", course: "一对一塑形", student: "陈晨", hours: "2 课时", score: "4.9", comment: "训练强度合适" }
];
const plans = ref(coachPlans.map((item) => ({ ...item })));
const showSchedule = ref(false);
const showPlan = ref(false);
const scheduleForm = reactive({ course_id: null, schedule_date: "", start_time: "", end_time: "", location: "" });
const planForm = reactive({ student: "", goal: "", part: "", action: "", sets: "", frequency: "" });

async function loadSchedules() {
  try {
    const res = await getSchedules();
    if (res.code === 0) {
      schedules.value = res.data || [];
    }
  } catch (e) {
    console.error("加载排课失败", e);
  }
}

async function loadCourses() {
  try {
    const res = await list_courses({ page: 1, page_size: 100 });
    if (res.code === 0) {
      courseOptions.value = res.data?.items || [];
    }
  } catch (e) {
    console.error("加载课程列表失败", e);
  }
}

onMounted(() => {
  loadSchedules();
  loadCourses();
});

function openSchedule() {
  showSchedule.value = true;
}

async function saveSchedule() {
  if (!scheduleForm.course_id || !scheduleForm.schedule_date || !scheduleForm.start_time || !scheduleForm.end_time) {
    toast.show("请填写完整排课信息");
    return;
  }
  try {
    const res = await addSchedule({
      course_id: scheduleForm.course_id,
      schedule_date: scheduleForm.schedule_date,
      start_time: scheduleForm.start_time + ":00",
      end_time: scheduleForm.end_time + ":00",
      location: scheduleForm.location,
      status: "未开始"
    });
    if (res.code === 0) {
      toast.show("排课已新增");
      showSchedule.value = false;
      scheduleForm.course_id = null;
      scheduleForm.schedule_date = "";
      scheduleForm.start_time = "";
      scheduleForm.end_time = "";
      scheduleForm.location = "";
      loadSchedules();
    } else {
      toast.show(res.msg || "排课失败");
    }
  } catch (e) {
    toast.show("排课失败，请重试");
    console.error(e);
  }
}

function checkSchedule(index) {
  schedules.value[index].status = "已签到";
  toast.show("签到完成");
}

function openPlan(item) {
  if (item) {
    planForm.student = item.name;
  } else {
    planForm.student = "";
  }
  showPlan.value = true;
}

function savePlan() {
  plans.value.unshift({ ...planForm });
  showPlan.value = false;
  toast.show("训练计划已保存");
}
</script>
