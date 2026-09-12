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
        <button class="btn btn-primary" type="button" @click="openSchedule()">新增排课</button>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard label="本月排课" v-model:value="summary.course_count" unit="节" icon="排" />
      <StatCard label="已授课时" v-model:value="summary.hours" unit="课时" icon="课" />
      <StatCard label="我的学员" v-model:value="summary.student_count" unit="人" icon="学" />
      <StatCard label="平均评分" v-model:value="summary.average_score" unit="分" icon="分" />
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
            <thead>
              <tr>
                <th>日期</th>
                <th>时段</th>
                <th>课程</th>
                <th>地点</th>
                <th>预约人数</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!schedules.length">
                <td colspan="7" style="text-align:center;color:#999;">暂无排课</td>
              </tr>
              <tr v-for="(item, index) in schedules" :key="item.id">
                <td>{{ item.schedule_date }}</td>
                <td>{{ item.start_time }} ~ {{ item.end_time }}</td>
                <td>{{ item.course_name }}</td>
                <td>{{ item.location }}</td>
                <td>{{ item.booked_count }} 人</td>
                <td>
                  <span class="badge" :class="item.status === '已签到' ? 'success' : item.status === '未开始' ? 'info' : 'warn'">
                    {{ item.status }}
                  </span>
                </td>
                <td>
                  <button class="btn btn-secondary btn-sm" type="button" @click="checkSchedule(index)">签到确认</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'students'" class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>学员</th>
                <th>手机号</th>
                <th>训练目标</th>
                <th>当前计划</th>
                <th>最近训练</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in students" :key="item.name">
                <td>{{ item.name }}</td>
                <td>{{ item.phone }}</td>
                <td>{{ item.goal }}</td>
                <td>{{ item.current_plan }}</td>
                <td>{{ item.recent_training }}</td>
                <td>
                  <button class="btn btn-secondary btn-sm" type="button" @click="openPlan(item)">制定计划</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'records'" class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>课程</th>
                <th>学员</th>
                <th>课时</th>
                <th>评分</th>
                <th>签到人数</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in records" :key="index">
                <td>{{ item.date }}</td>
                <td>{{ item.course }}</td>
                <td>{{ item.student }}</td>
                <td>{{ item.hours }}</td>
                <td>{{ item.score }}</td>
                <td>{{ item.comment }}</td>
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
            <thead>
              <tr>
                <th>id</th>
                <th>学员</th>
                <th>训练目标</th>
                <th>主要部位</th>
                <th>动作内容</th>
                <th>组数次数</th>
                <th>频率</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in plans" :key="item.id">
                <td>{{ item.member.id }}</td>
                <td>{{ item.member.name }}</td>
                <td>{{ item.goal }}</td>
                <td>{{ item.body_part }}</td>
                <td>{{ item.actions }}</td>
                <td>{{ item.sets_reps }}</td>
                <td>{{ item.frequency }}</td>
                <td>
                  <button class="btn btn-secondary btn-sm" type="button" @click="openPlan(item)">编辑</button>
                </td>
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
          <h3 class="panel-title">{{ planForm.id ? "编辑训练计划" : "制定训练计划" }}</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showPlan = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field">
              <label>学员id</label>
              <input v-model.number="planForm.member_id" step="1" placeholder="请输入学员的id" type="number" :disabled="!!planForm.id" />
            </div>
            <div class="field"><label>训练目标</label><input v-model="planForm.goal" type="text" placeholder="请输入训练目标"></div>
            <div class="field"><label>主要部位</label><input v-model="planForm.body_part" type="text" placeholder="请输入主要部位"></div>
            <div class="field"><label>动作内容</label><input v-model="planForm.actions" type="text"></div>
            <div class="field"><label>组数次数</label><input v-model="planForm.sets_reps" type="text" placeholder="比如:4 组 × 12 次"></div>
            <div class="field"><label>频率</label><input v-model="planForm.frequency" type="text" placeholder="每周 3 次"></div>
            <div class="field"><label>开始时间</label><input v-model="planForm.start_date" type="date"></div>
            <div class="field"><label>结束时间</label><input v-model="planForm.end_date" type="date"></div>
            <div class="field"><label>备注</label><input v-model="planForm.remark" type="text"></div>
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
import { coachStudents } from "../data/mock";
import { list_courses } from "../api/courses";
import StatCard from "../components/StatCard.vue";
import {
  create_training_plan,
  list_my_plans,
  update_training_plan,
  get_records,
  addSchedule,
  get_member
} from "../api/coach-panel.js";
import {create_schedule, list_schedule} from "../api/schedule.js";
import {getCoachStatistics} from "../api/statistics.js";

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
const students = ref([]);
const records = ref([]);
const plans = ref([]);
const showSchedule = ref(false);
const showPlan = ref(false);

const scheduleForm = reactive({
  course_id: null,
  schedule_date: "",
  start_time: "",
  end_time: "",
  location: ""
});

// 增加 id 字段，用于编辑；编辑时学员id禁用，不允许修改
const planForm = reactive({
  id: null,
  member_id: null,
  goal: "",
  body_part: "",
  actions: "",
  sets_reps: "",
  frequency: "",
  start_date: '',
  end_date: '',
  remark: ''
});

async function get_plans_list() {
  try {
    const res = await list_my_plans();
    console.log(res)
    plans.value = res.data;
  } catch (e) {
    console.error("加载训练计划失败", e);
  }
}

async function get_Schedules(){
  const res = await get_records();
  records.value = res.data;
  console.log(res)
}

async function get_my_member(){
  const res = await get_member();
  students.value = res.data;
  console.log(res)
}


async function loadSchedules() {
  try {
    const res = await list_schedule();
    console.log(res)
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
const summary = ref({
  average_score:null,
  course_count:null,
  student_count:null,
  hours:null
})
async function get_summary() {
  const res = await getCoachStatistics()
  summary.value.average_score = res.data[0].average_score
  summary.value.course_count = res.data[0].course_count
  summary.value.student_count = res.data[0].student_count
  summary.value.hours = res.data[0].hours
  console.log(res)
}

onMounted(async () => {
  await loadSchedules();
  await loadCourses();
  await get_plans_list();
  await get_Schedules();
  await get_my_member();
  await get_summary();
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
    const res = await create_schedule({
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

/**
 * 打开计划弹窗
 * @param {Object|null} item 学员对象 / plan对象；null=新增
 */
function openPlan(item) {
  // 清空表单
  planForm.id = null;
  planForm.member_id = null;
  planForm.goal = "";
  planForm.body_part = "";
  planForm.actions = "";
  planForm.sets_reps = "";
  planForm.frequency = "";
  planForm.start_date = "";
  planForm.end_date = "";
  planForm.remark = "";

  if (item) {
    // 来自学员表格：制定计划
    if (item.member === undefined) {
      planForm.member_id = item.id;
    } else {
      // 来自计划表格：编辑已有计划，回填数据
      planForm.id = item.id;
      planForm.member_id = item.member.id;
      planForm.goal = item.goal;
      planForm.body_part = item.body_part;
      planForm.actions = item.actions;
      planForm.sets_reps = item.sets_reps;
      planForm.frequency = item.frequency;
      planForm.start_date = item.start_date;
      planForm.end_date = item.end_date;
      planForm.remark = item.remark;
    }
  }
  showPlan.value = true;
}

async function savePlan() {
  try {
    if (planForm.id) {
      // 编辑模式
      const payload = {
        goal: planForm.goal,
        body_part: planForm.body_part,
        actions: planForm.actions,
        sets_reps: planForm.sets_reps,
        frequency: planForm.frequency,
        start_date: planForm.start_date,
        end_date: planForm.end_date,
        remark: planForm.remark
      };
      const res = await update_training_plan(planForm.id, payload);
      if (res.code !== 0) {
        toast.show(res.msg || "编辑失败");
        return;
      }
      toast.show("训练计划已更新");
    } else {
      // 新增模式
      const res = await create_training_plan(planForm);
      if (res.code !== 0) {
        toast.show(res.msg || "保存失败");
        return;
      }
      toast.show("训练计划已保存");
    }
    await get_plans_list();
    showPlan.value = false;
  } catch (err) {
    console.error(err);
    toast.show("操作失败，请重试");
  }
}
</script>