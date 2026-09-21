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
    </div>

    <div class="stat-grid">
      <StatCard label="排课总数" :value="summary.course_count" unit="节" icon="排" />
      <StatCard label="已授课时" :value="summary.hours" unit="课时" icon="课" />
      <StatCard label="我的学员" :value="summary.student_count" unit="人" icon="学" />
      <StatCard label="平均评分" :value="summary.average_score" unit="分" icon="分" />
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
        <!-- 排课不再手工新增：课程一建，就按课程的上课时间每周排好。
             这里把派生规则和窗口范围写清楚，免得教练以为「课少了」是数据丢了。 -->
        <p class="panel-note">
          排课按每门课程的上课时间每周自动生成：结束时间＝开始时间＋课程时长，地点继承课程。
          当前只显示 {{ scheduleWindow.label }}。签到按钮只在课程时段内出现，要调整课表点右侧「修改」。
        </p>
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
              <tr v-for="item in schedules" :key="item.id">
                <td>{{ dateWithWeekday(item.schedule_date) }}</td>
                <td>{{ item.start_time }} ~ {{ item.end_time }}</td>
                <td>{{ item.course_name }}</td>
                <td>{{ item.location }}</td>
                <td>{{ item.booked_count }} 人</td>
                <td>
                  <!-- 状态由后端按上课时间推导：未开始 / 进行中 / 已结束；
                       教练签到或取消会覆盖成人工状态 -->
                  <span class="badge" :class="scheduleStatusClass(item.status)">
                    {{ item.status }}
                  </span>
                </td>
                <td>
                  <div class="page-actions">
                    <!-- 签到按钮只在「进行中」出现。后端已经把状态按当前时间归正，
                         「进行中」= 此刻正处在课程时段内，而后端也只在这个窗口里放行签到
                         （没到点 / 已下课都会 400）。按钮不显示，好过点了才报错。 -->
                    <button v-if="item.status === '进行中'" class="btn btn-primary btn-sm" type="button" @click="checkSchedule(item)">签到确认</button>
                    <button v-else-if="item.status === '已签到'" class="btn btn-secondary btn-sm" type="button" @click="cancelSchedule(item)">撤销签到</button>
                    <!-- 已取消的排课改不了（后端会拦），要改先恢复 -->
                    <button v-else-if="item.status === '已取消'" class="btn btn-secondary btn-sm" type="button" @click="restoreSchedule(item)">恢复正常</button>
                    <button v-if="item.status !== '已取消'" class="btn btn-secondary btn-sm" type="button" @click="openScheduleEdit(item)">修改</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'students'" class="panel-body">
        <div class="page-actions" style="margin-bottom: 16px;">
          <button class="btn btn-primary" type="button" @click="openStudentForCreate">新增学员</button>
        </div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>学员</th>
                <th>性别/年龄</th>
                <th>手机号</th>
                <th>会员卡</th>
                <th>卡状态</th>
                <th>训练目标</th>
                <th>当前计划</th>
                <th>最近训练</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!students.length">
                <td colspan="9" style="text-align:center;color:#999;">暂无学员，点上方「新增学员」添加</td>
              </tr>
              <tr v-for="item in students" :key="item.member_id">
                <td>{{ item.name }}</td>
                <td>{{ genderAge(item) }}</td>
                <td>{{ item.phone }}</td>
                <td>{{ cardLabel(item) }}</td>
                <td>
                  <span class="badge" :class="cardStatusClass(item.status)">{{ item.status || '未开卡' }}</span>
                </td>
                <td>{{ item.goal || '-' }}</td>
                <td>{{ item.current_plan || '-' }}</td>
                <td>{{ item.recent_training || '-' }}</td>
                <td>
                  <button class="btn btn-secondary btn-sm" type="button" @click="openPlanForStudent(item)">制定计划</button>
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
                <th>备注</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!records.length">
                <td colspan="6" style="text-align:center;color:#999;">暂无授课记录</td>
              </tr>
              <tr v-for="(item, index) in records" :key="index">
                <td>{{ item.date }}</td>
                <td>{{ item.course }}</td>
                <td>{{ item.student }}</td>
                <td>{{ item.hours }}</td>
                <td>{{ item.score }}</td>
                <td>{{ item.comment || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else-if="activeTab === 'plans'" class="panel-body">
        <div class="page-actions" style="margin-bottom: 16px;">
          <button class="btn btn-primary" type="button" @click="openPlanForCreate()">新增训练计划</button>
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
              <tr v-if="!plans.length">
                <td colspan="8" style="text-align:center;color:#999;">暂无训练计划</td>
              </tr>
              <tr v-for="item in plans" :key="item.id">
                <td>{{ item.member_id }}</td>
                <td>{{ item.member?.name || item.member_name || '-' }}</td>
                <td>{{ item.goal }}</td>
                <td>{{ item.body_part }}</td>
                <td>{{ item.actions }}</td>
                <td>{{ item.sets_reps }}</td>
                <td>{{ item.frequency }}</td>
                <td>
                  <button class="btn btn-secondary btn-sm" type="button" @click="openPlanForEdit(item)">编辑</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else class="panel-body">
        <div class="form-grid" style="max-width: 760px;">
          <div class="field"><label>姓名</label><input v-model="profileForm.name" type="text"></div>
          <div class="field"><label>联系方式</label><input v-model="profileForm.phone" type="text"></div>
          <div class="field">
            <label>专长</label>
            <input v-model="profileForm.specialties" type="text" placeholder="如：力量训练,康复">
          </div>
        </div>
        <!-- 下面四项只读：在职状态与薪资由管理员维护，累计课时与平均评分来自系统统计，
             教练自己改不了（后端请求体里也根本不收这几个字段）。 -->
        <div class="form-grid" style="max-width: 760px; margin-top: 4px;">
          <div class="field"><label>入职时间</label><p class="field-hint">{{ profileInfo.hire_date || '-' }}</p></div>
          <div class="field"><label>在职状态</label><p class="field-hint">{{ profileInfo.status || '-' }}</p></div>
          <div class="field"><label>累计课时</label><p class="field-hint">{{ profileInfo.hours ?? 0 }} 课时</p></div>
          <div class="field"><label>平均评分</label><p class="field-hint">{{ profileInfo.score ?? '-' }} 分</p></div>
        </div>
        <p class="field-hint">
          姓名 / 联系方式 / 专长可以自己改；在职状态、课时与评分由管理员和系统统计维护。
        </p>
        <div class="page-actions" style="margin-top: 16px;">
          <button class="btn btn-primary" type="button" @click="saveProfile">保存资料</button>
          <button class="btn btn-secondary" type="button" @click="loadProfile">撤销修改</button>
        </div>
      </div>
    </div>

    <div v-if="showScheduleEdit" class="modal-mask" @click.self="showScheduleEdit = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">修改排课</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showScheduleEdit = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field">
              <!-- 课程不可改：排课是按课程时间派生的，换课程等于换一整套课表。
                   真换了课，重新在「课程与预约」里建课更清楚。 -->
              <label>课程</label>
              <input :value="scheduleEditForm.course_name" type="text" disabled>
            </div>
            <div class="field"><label>日期</label><input v-model="scheduleEditForm.schedule_date" type="date"></div>
            <div class="field"><label>开始时间</label>
              <input v-model="scheduleEditForm.start_time" type="time" @change="syncEndTime">
            </div>
            <div class="field"><label>结束时间</label><input v-model="scheduleEditForm.end_time" type="time"></div>
            <div class="field"><label>上课地点</label>
              <!-- 可选可填：点右侧箭头挑库里已有的教室，也可以直接手输新教室 -->
              <input v-model="scheduleEditForm.location" list="schedule-location-options" type="text" placeholder="可选可填，如：一号训练教室">
              <datalist id="schedule-location-options">
                <option v-for="loc in locationOptions" :key="loc" :value="loc" />
              </datalist>
            </div>
          </div>
          <p class="field-hint">
            只改这一次课，不影响课程本身。改完开始时间后，结束时间会按课程时长自动填入，也可以自己改。
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showScheduleEdit = false">取消</button>
          <button class="btn btn-primary" type="button" @click="saveScheduleEdit">保存</button>
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
              <!-- 原来是手填「学员id」。改成用「我的学员」接口的数据渲染下拉框：
                   学员表里本来就只有 member_id / name，教练不该去记编号。
                   编辑已有计划时学员不允许改（后端 PUT 也不收 member_id）。 -->
              <label>学员</label>
              <select v-model.number="planForm.member_id" :disabled="!!planForm.id">
                <option :value="null" disabled>请选择学员</option>
                <option v-for="s in studentOptions" :key="s.id" :value="s.id">{{ studentLabel(s) }}</option>
              </select>
            </div>
            <div class="field"><label>训练目标</label>
              <input v-model="planForm.goal" list="plan-goal-options" type="text" placeholder="可选可填，如：增肌">
              <datalist id="plan-goal-options">
                <option v-for="opt in planPresets.goal" :key="opt" :value="opt" />
              </datalist>
            </div>
            <div class="field"><label>主要部位</label>
              <input v-model="planForm.body_part" list="plan-body-part-options" type="text" placeholder="可选可填，如：背">
              <datalist id="plan-body-part-options">
                <option v-for="opt in planPresets.body_part" :key="opt" :value="opt" />
              </datalist>
            </div>
            <div class="field"><label>动作内容</label>
              <input v-model="planForm.actions" list="plan-actions-options" type="text" placeholder="可选可填，如：深蹲、硬拉">
              <datalist id="plan-actions-options">
                <option v-for="opt in planPresets.actions" :key="opt" :value="opt" />
              </datalist>
            </div>
            <div class="field"><label>组数次数</label>
              <input v-model="planForm.sets_reps" list="plan-sets-reps-options" type="text" placeholder="可选可填，如：4 组 × 12 次">
              <datalist id="plan-sets-reps-options">
                <option v-for="opt in planPresets.sets_reps" :key="opt" :value="opt" />
              </datalist>
            </div>
            <div class="field"><label>频率</label>
              <input v-model="planForm.frequency" list="plan-frequency-options" type="text" placeholder="可选可填，如：每周 3 次">
              <datalist id="plan-frequency-options">
                <option v-for="opt in planPresets.frequency" :key="opt" :value="opt" />
              </datalist>
            </div>
            <div class="field"><label>开始时间</label><input v-model="planForm.start_date" type="date"></div>
            <div class="field"><label>结束时间</label><input v-model="planForm.end_date" type="date"></div>
            <div class="field"><label>备注</label><input v-model="planForm.remark" type="text"></div>
          </div>
          <!-- 这几个字段是「预设有、也能自由填」：点输入框右侧箭头选常用值，
               也可以直接手打。真实训练内容不可能枚举完，所以不做成只读下拉。 -->
          <p class="field-hint">
            训练目标 / 主要部位 / 动作内容 / 组数次数 / 频率：可从下拉里挑常用值，也可直接自由输入。
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showPlan = false">取消</button>
          <button class="btn btn-primary" type="button" @click="savePlan">保存计划</button>
        </div>
      </div>
    </div>

    <div v-if="showStudent" class="modal-mask" @click.self="showStudent = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">新增学员</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showStudent = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field full">
              <label>搜索会员</label>
              <!-- 会员多起来以后光靠翻下拉框很费劲，先按姓名/手机号筛一遍 -->
              <input
                v-model="memberKeyword"
                type="search"
                placeholder="输入会员姓名或手机号筛选"
                @input="debounceMemberSearch"
              >
            </div>
            <div class="field full">
              <label>选择会员</label>
              <!-- 下拉框的选项来自数据库里已有的会员姓名（GET /coach-panel/member-options），
                   不再是手填姓名 —— 手填会造出同一个人的第二条档案，
                   而那条新档案没有登录账号，本人登不进会员中心。 -->
              <select v-model.number="studentForm.member_id">
                <option :value="null" disabled>请从已有会员中选择</option>
                <option v-for="m in memberOptions" :key="m.member_id" :value="m.member_id">
                  {{ memberOptionLabel(m) }}
                </option>
              </select>
            </div>
          </div>
          <p class="field-hint">
            学员从系统里已有的会员中选择（前台开卡或本人注册时都已经生成登录账号），
            选中的会员会直接挂到你的名下，不会再重复录一份档案。
          </p>
          <p v-if="!memberOptions.length" class="field-hint">
            暂时没有可添加的会员：未分配的会员都已在你名下，或已被其他教练认领。
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showStudent = false">取消</button>
          <button class="btn btn-primary" type="button" @click="saveStudent">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from "vue";
import { useToast } from "../composables/useToast";
import { list_course_locations } from "../api/courses.js";
import StatCard from "../components/StatCard.vue";
import {
  assign_coach_student,
  create_training_plan,
  get_member,
  get_member_options,
  get_my_profile,
  get_records,
  get_schedule_window,
  list_my_plans,
  list_plan_presets,
  list_schedule,
  update_my_profile,
  update_schedule,
  update_schedule_status,
  update_training_plan
} from "../api/coach-panel.js";
import { getCoachStatistics } from "../api/statistics.js";

const toast = useToast();
const activeTab = ref("schedule");
const tabs = [
  { key: "schedule", label: "我的排课" },
  { key: "students", label: "我的学员" },
  { key: "records", label: "授课记录" },
  { key: "plans", label: "训练计划" },
  { key: "profile", label: "个人资料" }
];
const schedules = ref([]);
// 上课地点候选：来自 GET /courses/locations（课程表 + 排课表里用过的教室）。
// 地点仍可自由输入（可能新开教室），这里只是给出库里已有的叫法。
const locationOptions = ref([]);
// 排课窗口（今天前后各 2 周）：区间由后端算好返回，前端不自己推天数
const scheduleWindow = ref({ start: "", end: "", label: "最近 4 周的排课" });
const students = ref([]);
const records = ref([]);
const plans = ref([]);
const showScheduleEdit = ref(false);
const showPlan = ref(false);
const showStudent = ref(false);

// 修改排课的草稿。时间用 <input type="time"> 的 HH:mm，提交时再补 ":00"
const scheduleEditForm = reactive({
  id: null,
  course_name: "",
  duration: null,
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

// 新增学员的草稿：只记「选了哪一位会员」。
// 会员档案（姓名/手机号/卡类型/余额/卡状态）全部来自库里已有的那条记录，
// 教练不在这里录，也就不会再产生没有登录账号的会员。
const studentForm = reactive({
  member_id: null
});

// 「新增学员」下拉框的候选会员：未归属教练的 + 已经归属自己的
const memberOptions = ref([]);
const memberKeyword = ref("");

/** 下拉选项文案：姓名 · 手机号 · 卡类型/状态，尽量一屏看清是谁 */
function memberOptionLabel(member) {
  const parts = [member.name];
  if (member.phone) parts.push(member.phone);
  const card = [member.card_type, member.status].filter(Boolean).join("·");
  if (card) parts.push(card);
  return parts.join(" · ");
}

/** 加载可添加的会员。keyword 传空即取全部（后端按姓名/手机号模糊匹配） */
async function loadMemberOptions(keyword = "") {
  try {
    const res = await get_member_options({ keyword: keyword || undefined });
    memberOptions.value = res.data || [];
  } catch (err) {
    toast.show(err.friendlyMessage || "加载会员列表失败", "error");
  }
}

// 搜索防抖：下拉框要跟着输入实时筛，但不能每敲一个字就打一次接口
let memberSearchTimer = null;
const MEMBER_SEARCH_DELAY = 350;

function debounceMemberSearch() {
  if (memberSearchTimer) clearTimeout(memberSearchTimer);
  memberSearchTimer = setTimeout(() => {
    loadMemberOptions(memberKeyword.value.trim());
  }, MEMBER_SEARCH_DELAY);
}

// 个人资料：可改的三项 + 只读展示的原始资料（入职时间/状态/课时/评分）
const profileInfo = ref({});
const profileForm = reactive({
  name: "",
  phone: "",
  specialties: ""
});

// 训练计划「预设 + 自由输入」的兜底候选。
// 正常情况下由 GET /coach-panel/plan-presets 覆盖（body_part 还来自管理员维护的
// sys_dict）；接口挂了就用这份内置值，保证弹窗永远有东西可选、不至于空着。
const FALLBACK_PLAN_PRESETS = {
  goal: ["增肌", "减脂", "塑形", "提升力量", "改善体态", "提升耐力", "康复训练"],
  body_part: ["胸", "背", "腿", "肩", "核心", "手臂"],
  actions: ["深蹲", "卧推", "硬拉", "引体向上", "俯卧撑", "坐姿划船", "高位下拉", "平板支撑"],
  sets_reps: ["3 组 × 12 次", "4 组 × 10 次", "5 组 × 5 次", "3 组 × 15 次"],
  frequency: ["每周 1 次", "每周 2 次", "每周 3 次", "每周 4 次", "每周 5 次"]
};

const planPresets = reactive({ ...FALLBACK_PLAN_PRESETS });

/**
 * 加载训练计划的预设候选值。
 * body_part 由后端从 sys_dict 取（管理员可在系统设置里维护）；
 * 其余字段库里没有字典，用后端常量。
 */
async function loadPlanPresets() {
  try {
    const res = await list_plan_presets();
    const data = res.data || {};
    Object.keys(FALLBACK_PLAN_PRESETS).forEach(key => {
      const values = data[key];
      if (Array.isArray(values) && values.length) {
        planPresets[key] = values;
      }
    });
  } catch (err) {
    // 静默降级：用内置兜底值，不打断教练填表单
    console.warn("加载训练计划预设失败，使用内置候选值：", err?.friendlyMessage || err);
  }
}

/**
 * 训练计划弹窗的学员下拉选项。
 * 数据源是「我的学员」接口（字段是 member_id，不是 id）。
 * 编辑一张不在当前学员列表里的计划时，把该计划原本的会员补进选项，
 * 否则下拉框会因为没有匹配项而显示空白。
 */
const studentOptions = computed(() => {
  const list = students.value.map(s => ({ id: s.member_id, name: s.name, phone: s.phone }));
  if (planForm.member_id && !list.some(s => s.id === planForm.member_id)) {
    const current = plans.value.find(p => p.id === planForm.id);
    list.unshift({
      id: planForm.member_id,
      name: current?.member?.name || current?.member_name || `会员 #${planForm.member_id}`,
      phone: ""
    });
  }
  return list;
});

/** 下拉框显示文案：把「姓名 · 手机号」拼好，避免在 <option> 里嵌套条件模板 */
function studentLabel(student) {
  return student.phone ? `${student.name} · ${student.phone}` : student.name;
}

/** 加载训练计划列表（接口返回裸数组） */
async function loadPlans() {
  try {
    const res = await list_my_plans();
    plans.value = res.data || [];
  } catch (err) {
    toast.show(err.friendlyMessage || "加载训练计划失败", "error");
  }
}

/** 加载授课记录 */
async function loadRecords() {
  try {
    const res = await get_records();
    records.value = res.data || [];
  } catch (err) {
    toast.show(err.friendlyMessage || "加载授课记录失败", "error");
  }
}

/** 加载我的学员 */
async function loadStudents() {
  try {
    const res = await get_member();
    students.value = res.data || [];
  } catch (err) {
    toast.show(err.friendlyMessage || "加载学员列表失败", "error");
  }
}

/** 加载我的排课。后端返回的 status 已按当前时间归正（未开始/进行中/已结束…） */
async function loadSchedules() {
  try {
    const res = await list_schedule();
    schedules.value = res.data || [];
  } catch (err) {
    toast.show(err.friendlyMessage || "加载排课失败", "error");
  }
}

/**
 * 加载上课地点候选。
 * 同一个教室被写成「三号训练教室」「三号教室」两种叫法时，统计和筛选都对不上，
 * 所以给一份库里已有的叫法。地点本身仍可自由输入（新开教室不用改代码）。
 */
async function loadLocations() {
  try {
    const res = await list_course_locations();
    locationOptions.value = res.data || [];
  } catch (err) {
    toast.show(err.friendlyMessage || "加载上课地点失败", "error");
  }
}

/**
 * 加载排课窗口的起止日期。
 * 窗口天数（前后各 2 周）只写在后端一处，前端拿它显示范围，
 * 不在两边各算一遍 —— 否则改天数时必然漏改一边。
 */
async function loadScheduleWindow() {
  try {
    const res = await get_schedule_window();
    const data = res.data || {};
    scheduleWindow.value = {
      start: data.start || "",
      end: data.end || "",
      label: data.start && data.end ? `${data.start} ~ ${data.end}` : "最近 4 周的排课"
    };
  } catch (err) {
    // 只是标题文案，取不到就用兜底串，不打断排课列表
    console.warn("加载排课窗口失败：", err?.friendlyMessage || err);
  }
}

/** 排课状态 → 徽标配色。五个状态各用一色，扫一眼就能分清「待上课 / 上课中 / 上完了」 */
function scheduleStatusClass(status) {
  if (status === "未开始") return "warn"; // 待上课，需要留意
  if (status === "进行中") return "info"; // 正在上课
  if (status === "已签到") return "success"; // 已确认到场
  if (status === "已取消") return "danger"; // 异常终止
  return "muted"; // 已结束：不用管了，用最轻的灰
}

/** 日期后面带上星期几，一眼能看出这周还有几节课（周几由日期推出来，不用后端给） */
function dateWithWeekday(value) {
  if (!value) return "-";
  const base = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(base.getTime())) return value;
  return `${String(value).slice(0, 10)} 周${"日一二三四五六"[base.getDay()]}`;
}

/** 学员「性别/年龄」单元格：任意一项缺失都不显示英文 null/undefined */
function genderAge(item) {
  const parts = [item.gender, item.age ? `${item.age} 岁` : ""].filter(Boolean);
  return parts.length ? parts.join(" · ") : "-";
}

/** 学员「会员卡」单元格：卡种 + 到期日，没开卡就直说 */
function cardLabel(item) {
  if (!item.card_type) return "未开卡";
  return item.card_expire ? `${item.card_type}（${String(item.card_expire).slice(0, 10)} 到期）` : item.card_type;
}

/** 卡状态 → 徽标配色。与会员管理页口径一致：正常绿、快到期/暂停黄、过期红 */
function cardStatusClass(status) {
  if (status === "正常") return "success";
  if (status === "暂停") return "warn";
  if (status === "过期") return "danger";
  return "muted";
}

const summary = ref({
  average_score: 0,
  course_count: 0,
  student_count: 0,
  hours: 0
});

/** 加载工作台统计卡片；没有统计数据时保持 0，不能让 data[0] 报错 */
async function loadSummary() {
  try {
    const res = await getCoachStatistics();
    const data = Array.isArray(res.data) ? res.data[0] : res.data;
    if (!data) return;
    summary.value.average_score = Math.round((data.average_score ?? 0) * 10) / 10;
    summary.value.course_count = data.course_count ?? 0;
    summary.value.student_count = data.student_count ?? 0;
    summary.value.hours = data.hours ?? 0;
  } catch (err) {
    toast.show(err.friendlyMessage || "加载统计数据失败", "error");
  }
}

onMounted(async () => {
  await loadSchedules();
  await loadScheduleWindow();
  await loadLocations();
  await loadPlanPresets();
  await loadPlans();
  await loadRecords();
  await loadStudents();
  await loadProfile();
  await loadSummary();
});

/** "HH:mm:ss"（后端 time）→ "HH:mm"（<input type="time"> 只认这个） */
function toTimeInput(value) {
  return value ? String(value).slice(0, 5) : "";
}

/** "HH:mm" → "HH:mm:00"，后端收的是 time */
function toBackendTime(value) {
  if (!value) return null;
  const text = String(value);
  return text.length === 5 ? `${text}:00` : text;
}

/** "HH:mm" 加分钟数，用于按课程时长自动补结束时间 */
function addMinutes(value, minutes) {
  if (!value) return "";
  const [hour, minute] = String(value).split(":").map(Number);
  if (Number.isNaN(hour) || Number.isNaN(minute)) return "";
  const total = (hour * 60 + minute + Number(minutes || 0)) % (24 * 60);
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

/** 打开「修改排课」：回填当前排课，课程只读展示 */
async function openScheduleEdit(item) {
  scheduleEditForm.id = item.id;
  scheduleEditForm.course_name = item.course_name || "";
  scheduleEditForm.duration = item.duration ?? null;
  scheduleEditForm.schedule_date = item.schedule_date || "";
  scheduleEditForm.start_time = toTimeInput(item.start_time);
  scheduleEditForm.end_time = toTimeInput(item.end_time);
  scheduleEditForm.location = item.location || "";
  if (!locationOptions.value.length) {
    await loadLocations();
  }
  showScheduleEdit.value = true;
}

/**
 * 改了开始时间就按课程时长顺推结束时间。
 * 只填不改也行 —— 结束时段的输入框始终可编辑，这里只是省一次手算。
 */
function syncEndTime() {
  const duration = scheduleEditForm.duration;
  if (!scheduleEditForm.start_time || !duration) return;
  scheduleEditForm.end_time = addMinutes(scheduleEditForm.start_time, duration);
}

/** 保存修改：日期 / 时段 / 地点都提交，课程不提交（后端也不收） */
async function saveScheduleEdit() {
  if (!scheduleEditForm.schedule_date || !scheduleEditForm.start_time || !scheduleEditForm.end_time) {
    toast.show("请填写完整的日期与时段", "error");
    return;
  }
  if (!scheduleEditForm.location.trim()) {
    toast.show("请填写上课地点", "error");
    return;
  }
  if (scheduleEditForm.end_time <= scheduleEditForm.start_time) {
    toast.show("结束时间必须晚于开始时间", "error");
    return;
  }
  try {
    const res = await update_schedule(scheduleEditForm.id, {
      schedule_date: scheduleEditForm.schedule_date,
      start_time: toBackendTime(scheduleEditForm.start_time),
      end_time: toBackendTime(scheduleEditForm.end_time),
      location: scheduleEditForm.location.trim()
    });
    // 后端改期会把这条排课名下预约的上课时间一起挪，msg 里带着同步条数，
    // 原样呈现给教练 —— 否则他只看到自己的课表变了，不知道已报名的会员那边也变了
    toast.show((res && res.msg) || "排课已修改");
    showScheduleEdit.value = false;
    await loadSchedules();
  } catch (err) {
    toast.show(err.friendlyMessage || "修改失败，请重试", "error");
  }
}

/** 把已取消的排课恢复成正常（改时间地点前必须先恢复，后端会拦） */
async function restoreSchedule(item) {
  try {
    await update_schedule_status(item.id, "未开始");
    toast.show("已恢复正常");
    await loadSchedules();
  } catch (err) {
    toast.show(err.friendlyMessage || "恢复失败", "error");
  }
}

/** 签到确认：调用接口改排课状态，并刷新列表 */
async function checkSchedule(item) {
  try {
    await update_schedule_status(item.id, "已签到");
    toast.show("签到完成");
    await loadSchedules();
  } catch (err) {
    toast.show(err.friendlyMessage || "签到失败", "error");
  }
}

/** 撤销签到：把排课状态改回未开始 */
async function cancelSchedule(item) {
  try {
    await update_schedule_status(item.id, "未开始");
    toast.show("已撤销签到");
    await loadSchedules();
  } catch (err) {
    toast.show(err.friendlyMessage || "撤销失败", "error");
  }
}

function resetPlanForm() {
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
}

/** 新增计划：学员从「我的学员」下拉框里选 */
async function openPlanForCreate() {
  resetPlanForm();
  // 首屏加载失败时补一次，否则 datalist 只有内置兜底值
  if (!planPresets.goal.length) {
    await loadPlanPresets();
  }
  showPlan.value = true;
}

/** 从学员表格发起：学员对象上的字段是 member_id，不是 id */
function openPlanForStudent(student) {
  resetPlanForm();
  planForm.member_id = student.member_id;
  showPlan.value = true;
}

function resetStudentForm() {
  studentForm.member_id = null;
  memberKeyword.value = "";
}

/**
 * 打开「新增学员」：拉一次可添加的会员列表，下拉框里就是数据库里的会员姓名。
 * 每次都重新拉：别人刚开卡 / 刚被其他教练认领，选项要跟着变。
 */
async function openStudentForCreate() {
  resetStudentForm();
  showStudent.value = true;
  await loadMemberOptions();
}

/**
 * 保存：把选中的会员挂到自己名下。
 * 后端只收 member_id —— 会员档案与登录账号在开卡/注册时就已经建好，
 * 这里不重复录，也就不会造出「有档案没账号」的人。
 */
async function saveStudent() {
  if (!studentForm.member_id) {
    toast.show("请选择要添加的会员", "error");
    return;
  }
  try {
    const res = await assign_coach_student(studentForm.member_id);
    toast.show(res.msg || "学员已添加");
    showStudent.value = false;
    // 学员列表与统计卡片（我的学员人数）都要跟着更新
    await Promise.all([loadStudents(), loadSummary()]);
  } catch (err) {
    toast.show(err.friendlyMessage || "添加学员失败，请重试", "error");
  }
}

/** 加载个人资料：可改的三项填进表单，其余字段只读展示 */
async function loadProfile() {
  try {
    const res = await get_my_profile();
    const data = res.data || {};
    profileInfo.value = data;
    profileForm.name = data.name || "";
    profileForm.phone = data.phone || "";
    profileForm.specialties = data.specialties || "";
  } catch (err) {
    toast.show(err.friendlyMessage || "加载个人资料失败", "error");
  }
}

/**
 * 保存个人资料。
 * 只提交姓名 / 联系方式 / 专长 —— 在职状态、薪资、课时、评分由管理员与系统维护，
 * 后端请求体里也没有这几项，这里多传不会有任何作用。
 */
async function saveProfile() {
  if (!profileForm.name.trim()) {
    toast.show("请填写姓名", "error");
    return;
  }
  if (!profileForm.phone.trim()) {
    toast.show("请填写联系方式", "error");
    return;
  }
  if (!profileForm.specialties.trim()) {
    toast.show("请填写专长", "error");
    return;
  }
  try {
    const res = await update_my_profile({
      name: profileForm.name.trim(),
      phone: profileForm.phone.trim(),
      specialties: profileForm.specialties.trim()
    });
    // 用后端返回的档案回填（姓名已 strip，展示也要跟着同步）
    const data = res.data || {};
    profileInfo.value = data;
    profileForm.name = data.name || profileForm.name;
    profileForm.phone = data.phone || profileForm.phone;
    profileForm.specialties = data.specialties || profileForm.specialties;
    toast.show("资料已更新");
  } catch (err) {
    toast.show(err.friendlyMessage || "保存失败，请重试", "error");
  }
}

/** 从计划表格发起：编辑已有计划，回填数据 */
function openPlanForEdit(plan) {
  resetPlanForm();
  planForm.id = plan.id;
  planForm.member_id = plan.member_id ?? plan.member?.id ?? null;
  planForm.goal = plan.goal;
  planForm.body_part = plan.body_part;
  planForm.actions = plan.actions;
  planForm.sets_reps = plan.sets_reps;
  planForm.frequency = plan.frequency;
  planForm.start_date = plan.start_date;
  planForm.end_date = plan.end_date;
  planForm.remark = plan.remark;
  showPlan.value = true;
}

async function savePlan() {
  if (!planForm.member_id) {
    toast.show("请选择学员", "error");
    return;
  }
  if (!planForm.goal || !planForm.body_part || !planForm.actions
    || !planForm.sets_reps || !planForm.frequency) {
    toast.show("请填写完整的训练计划内容", "error");
    return;
  }
  if (!planForm.start_date || !planForm.end_date) {
    toast.show("请选择开始与结束日期", "error");
    return;
  }
  if (planForm.end_date < planForm.start_date) {
    toast.show("结束日期不能早于开始日期", "error");
    return;
  }
  try {
    if (planForm.id) {
      // 编辑模式：member_id 不允许改，请求体里也不带
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
      await update_training_plan(planForm.id, payload);
      toast.show("训练计划已更新");
    } else {
      // 新增模式
      await create_training_plan(planForm);
      toast.show("训练计划已保存");
    }
    await loadPlans();
    showPlan.value = false;
  } catch (err) {
    toast.show(err.friendlyMessage || "操作失败，请重试", "error");
  }
}
</script>