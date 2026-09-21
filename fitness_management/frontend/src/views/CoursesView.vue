<template>
  <div>
    <transition name="fade">
      <div v-if="toast.message" class="toast-banner" :class="toast.type">{{ toast.message }}</div>
    </transition>

    <div class="page-header">
      <div>
        <h1>{{ pageTitle }}</h1>
        <p class="page-desc">{{ pageDesc }}</p>
      </div>
      <div class="page-actions">
        <button v-if="canManage" class="btn btn-primary" type="button" @click="openAdd">新增课程</button>
      </div>
    </div>

    <div class="panel">
      <!-- 搜索栏 -->
      <div class="panel-search" style="display:flex;gap:12px;align-items:center;padding:16px;">
        <input
          v-model="queryForm.keyword"
          type="text"
          placeholder="输入课程名称/教练姓名搜索"
          style="padding:6px 8px;width:260px;"
          @keyup.enter="loadData"
        />
        <button class="btn btn-primary" @click="loadData">搜索</button>
        <button class="btn btn-secondary" @click="resetSearch">重置</button>
      </div>

      <div class="tabs">
        <button class="tab-btn" :class="{ active: activeTab === 'all' }" type="button" @click="handleTabChange('all')">{{ tabLabels.all }}</button>
        <button class="tab-btn" :class="{ active: activeTab === 'group' }" type="button" @click="handleTabChange('group')">公共团课</button>
        <button class="tab-btn" :class="{ active: activeTab === 'private' }" type="button" @click="handleTabChange('private')">私教课程</button>
      </div>

      <!-- 会员：课表来自教练排课（不是课程表里的时间模板） -->
      <div v-if="isMember" class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>上课日期</th>
                <th>星期</th>
                <th>时间段</th>
                <th>课程名称</th>
                <th>分类</th>
                <th>授课教练</th>
                <th>上课地点</th>
                <th>已约/上限</th>
                <th>课程类型</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!scheduleList.length">
                <td colspan="11" style="text-align:center;color:#999;">近期暂无可预约的排课</td>
              </tr>
              <tr v-for="item in scheduleList" :key="item.schedule_id">
                <td>{{ item.schedule_date }}</td>
                <td>{{ weekdayOf(item.schedule_date) }}</td>
                <td>{{ formatClock(item.start_time) }} ~ {{ formatClock(item.end_time) }}</td>
                <td>{{ item.course_name }}</td>
                <td>{{ item.category || '-' }}</td>
                <td>{{ item.coach_name || '-' }}</td>
                <td>{{ item.location || '-' }}</td>
                <td>{{ item.booked_count || 0 }} / {{ headcountLimit(item) }}</td>
                <td>{{ item.course_type === 'private' ? '私教' : '团课' }}</td>
                <td><span class="badge" :class="scheduleStatusClass(item.status)">{{ item.status }}</span></td>
                <td>
                  <!-- 已经约过的直接标出来，不给第二个「预约」按钮去撞后端的重复预约校验 -->
                  <span v-if="item.booked_by_me" class="badge success">已预约</span>
                  <button v-else-if="item.can_book" class="btn btn-primary btn-sm" type="button" @click="bookSchedule(item)">预约</button>
                  <span v-else style="color:#999;">不可预约</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pagination-bar" style="padding:12px 16px;">
          <span>共 {{ scheduleList.length }} 节排课（今天起 4 周内）</span>
        </div>
      </div>

      <!-- 管理员 / 前台 / 教练：课程维护列表 -->
      <div v-else class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>课程名称</th>
                <th>分类</th>
                <th>授课教练</th>
                <th>课时时长</th>
                <th>上课时间</th>
                <th>上课地点</th>
                <th>课时单价</th>
                <th>已约/上限</th>
                <th>课程类型</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in currentList" :key="item.id">
                <td>{{ item.name }}</td>
                <td>{{ item.category || '-' }}</td>
                <td>{{ item.coach_name }}</td>
                <td>{{ item.duration }} 分钟</td>
                <td>{{ item.start_time || '-' }}</td>
                <td>{{ item.location || '-' }}</td>
                <td>¥ {{ item.price }}</td>
                <!-- 团课看最大人数，私教看私教会员名额 -->
                <td>{{ item.booked_count }} / {{ headcountLimit(item) }}</td>
                <td>{{ item.course_type === 'private' ? '私教' : '团课' }}</td>
                <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
                <td>
                  <div class="page-actions">
                    <!-- ==========新增编辑按钮========== -->
                    <button v-if="canManage" class="btn btn-secondary btn-sm" type="button" @click="openEdit(item)">编辑</button>

                    <button v-if="canManage" class="btn btn-secondary btn-sm" type="button" @click="toggle(item)">
                      {{ item.status === '已下架' ? '上架' : '下架' }}
                    </button>
                    <button v-if="canManage" class="btn btn-danger btn-sm" type="button" @click="remove(item)">删除</button>
                    <button v-if="canManage " class="btn btn-secondary btn-sm" type="button" @click="openReservation(item)">预约名单</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页组件 -->
        <div class="pagination-bar" style="padding:12px 16px;display:flex;gap:10px;align-items:center;">
          <span>共 {{ total }} 条</span>
          <button class="btn btn-secondary btn-sm" :disabled="queryForm.page <=1" @click="prevPage">上一页</button>
          <span>第 {{ queryForm.page }} 页</span>
          <button class="btn btn-secondary btn-sm" :disabled="queryForm.page * queryForm.page_size >= total" @click="nextPage">下一页</button>
        </div>
      </div>
    </div>

    <!-- =========新增/编辑共用弹窗 isEdit区分模式========== -->
    <div v-if="showAdd" class="modal-mask" @click.self="showAdd = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">{{ isEdit ? '编辑课程' : '新增课程' }}</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showAdd = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field full"><label>课程名称</label><input v-model="courseForm.name" type="text"></div>
            <div class="field"><label>授课教练</label>
              <!-- 原来是手填「授课教练ID」，用户得先知道教练编号才能建课。
                   改成从教练列表接口拉数据渲染，显示姓名、提交回传 id。 -->
              <select v-model.number="courseForm.coach_id">
                <option :value="null" disabled>请选择授课教练</option>
                <option v-for="c in coachOptions" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select></div>
            <div class="field"><label>课程分类</label>
              <select v-model="courseForm.category">
                <option value="瑜伽">瑜伽</option>
                <option value="搏击">搏击</option>
                <option value="普拉提">普拉提</option>
                <option value="力量训练">力量训练</option>
                <option value="有氧">有氧</option>
                <option value="综合体能">综合体能</option>
                <option value="康复">康复</option>
                <option value="球类体能">球类体能</option>
                <option value="少儿">少儿</option>
              </select></div>
            <div class="field"><label>时长(分钟)</label><input v-model.number="courseForm.duration" type="number"></div>
            <div class="field"><label>价格</label><input v-model.number="courseForm.price" type="number"></div>
            <div class="field"><label>上课时间</label><input v-model="courseForm.start_time" type="datetime-local"></div>
            <div class="field"><label>上课地点</label>
              <!-- 可选可填：点右侧箭头挑库里已有的教室，也可以直接手输 -->
              <input v-model="courseForm.location" list="course-location-options" type="text" placeholder="可选可填，如：一号训练教室">
              <datalist id="course-location-options">
                <option v-for="loc in locationOptions" :key="loc" :value="loc" />
              </datalist>
            </div>
            <div class="field"><label>课程类型</label><select v-model="courseForm.course_type">
              <option value="group">团课</option>
              <option value="private">私教课</option>
            </select></div>
             <div class="field"><label>最大人数</label><input v-model.number="courseForm.max_count" type="number"></div>
            <div class="field"><label>私教会员名额</label><input v-model.number="courseForm.capacity" type="number"></div>
            <div class="field">
              <label>状态</label>
              <select v-model="courseForm.status">
                <option>已上架</option>
                <option>已下架</option>
              </select>
            </div>
          </div>
          <!-- 这三个字段不只影响课程本身：教练工作台的排课是按它们派生的 -->
          <p class="field-hint">
            上课时间只取「星期几 + 时刻」：教练工作台会按它每周自动排出课表，
            结束时间由「时长」推出，地点也一并带到排课里。
            只改价格、名称这类字段不会影响已经排好的课。
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showAdd = false">取消</button>
          <button class="btn btn-primary" type="button" @click="saveCourse">{{ isEdit ? '更新' : '保存' }}</button>
        </div>
      </div>
    </div>

    <div v-if="showReservation" class="modal-mask" @click.self="showReservation = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">预约名单：{{ selectedCourse && selectedCourse.name }}</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showReservation = false">关闭</button>
        </div>
        <div class="modal-body no-padding">
          <div class="data-table-wrap">
            <table class="data-table">
              <thead>
                <tr><th>会员</th><th>手机号</th><th>预约时间</th><th>状态</th></tr>
              </thead>
              <tbody>
                <tr v-for="item in reservationList" :key="item.member">
                  <td>{{ item.member }}</td>
                  <td>{{ item.phone }}</td>
                  <td>{{ item.appointment_time }}</td>
                  <td><span class="badge" :class="item.status === '已签到' ? 'success' : 'info'">{{ item.status }}</span></td>
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
import { computed, reactive, ref, onMounted } from "vue";
import { useAuth } from "../composables/useAuth";
import { useToast } from "../composables/useToast";
import { confirmDialog } from "../composables/useConfirm.js";
import {create_courses, delete_courses, list_course_locations, list_courses, list_course_schedules, toggle_courses, update_courses,get_course_appointments} from "../api/courses.js";
import { create_appointment } from "../api/appointments.js";
import { scheduleStatusClass } from "../utils/appointmentStatus.js";
import { getCoachList } from "../api/coach";
import { useUserStore } from "../stores/user.js";

const useStore = useUserStore();
const auth = useAuth();
const toast = useToast();
// 用 computed：解构出来的 role 是一次性快照，同一页面内切换身份不会跟着更新
const role = computed(() => useStore.role);
const canManage = computed(() => ["admin", "reception", "coach"].includes(role.value));
/** 会员看到的不是课程表，而是教练排出来的「具体某一次课」 */
const isMember = computed(() => role.value === "member");

/** 课程人数上限：团课看 max_count，私教看私教会员名额 capacity */
function headcountLimit(item) {
  const limit = item.course_type === "private" ? item.capacity : item.max_count;
  return limit ?? "-";
}

/** 排课的日期 → 星期几，会员扫一眼就知道是周几的课 */
function weekdayOf(dateStr) {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return "-";
  return "周" + "日一二三四五六"[d.getDay()];
}

/** 排课时段：后端给的是 "08:01:00"，列里只显示到分 */
function formatClock(value) {
  if (!value) return "-";
  return String(value).slice(0, 5);
}

const activeTab = ref("all");
const showAdd = ref(false);
const showReservation = ref(false);
const selectedCourse = ref(null);

/** 会员看的是排课，标签文案跟着换，免得「所有课程」和下面的课表对不上 */
const tabLabels = computed(() => (
  isMember.value ? { all: "全部排课" } : { all: "所有课程" }
));

// =========编辑状态变量==========
const isEdit = ref(false);
const editCourseId = ref(null);

// 查询参数：对接后端crud
const queryForm = reactive({
  keyword: "",
  page: 1,
  page_size: 10,
  course_type: "",
  category: "",
  status: "",
  coach_id: ""
});

// 新增/编辑共用表单
const courseForm = ref({
  name: "",
  course_type: null,
  category: null,
  location: "",
  coach_id: null,
  start_time: null,
  duration: null,
  max_count: null,
  capacity:null,
  price: null,
  status: "已上架"
});

const total = ref(0);
const tableData = ref([]);
/** 会员看到的课表：全部教练在窗口内的排课（含上课地点、可约/已满） */
const scheduleList = ref([]);
/** 授课教练下拉框数据源（显示姓名，提交 coach_id） */
const coachOptions = ref([]);
/** 上课地点候选：库里用过的教室名，可选可填（地点仍允许自由输入） */
const locationOptions = ref([]);

/**
 * 加载上课地点候选（课程表 + 排课表里出现过的教室名）。
 * 地点会影响教练排课，是排课的派生源之一，所以和教练列表一起在进页面时取好。
 */
async function loadLocations() {
  if (!canManage.value) return;
  try {
    const res = await list_course_locations();
    locationOptions.value = res.data || [];
  } catch (err) {
    // 只是输入建议，取不到不影响填表单，不弹提示打断
    console.warn("加载上课地点候选失败：", err?.friendlyMessage || err);
  }
}

// 当前页面列表
const currentList = computed(() => tableData.value);

const reservationList = ref([])

const pageTitle = computed(() => {
  // 这几行原来写的是 `role === "reception"`：role 是 computed ref，
  // 在 <script setup> 里直接跟字符串比永远不相等 → 标题和描述恒为管理员那套文案。
  // 模板里能这么写是因为 Vue 会自动解包 ref，脚本里必须用 role.value。
  if (role.value === "reception") return "预约处理";
  if (role.value === "coach") return "课程中心";
  if (role.value === "member") return "预约课程";
  return "课程与预约";
});

const pageDesc = computed(() => {
  if (role.value === "member") return "按教练排出的课表选课：每天有哪些课、在哪上、还有没有名额都在这。";
  if (role.value === "coach") return "查看课程信息、预约人数和授课安排。";
  if (role.value === "reception") return "处理课程预约、取消预约和会员签到。";
  return "维护公共团课、私教课程和会员预约记录。";
});

function statusClass(status) {
  if (status === "已上架") return "success";
  if (status === "已满员") return "warn";
  return "muted";
}

/**
 * 加载列表。两种角色看的是两套数据，分派就在这里：
 * 会员 = 教练排出的具体课表；其余角色 = 课程维护列表。
 */
async function loadData() {
  if (isMember.value) {
    await loadSchedules();
    return;
  }
  try {
    const params = { ...queryForm };
    Object.keys(params).forEach(k => {
      if (params[k] === "") params[k] = undefined;
    });
    const res = await list_courses(params);
    tableData.value = res.data.items;
    total.value = res.data.total;
  } catch (err) {
    toast.show(err.friendlyMessage || "加载课程列表失败", "error");
  }
}

/**
 * 会员课表：GET /courses/schedules —— 全部教练、从今天起往后 4 周的排课。
 * 排课的课程/分类/教练/时间/地点/容量都由后端一次给全，前端只负责展示；
 * 「能不能约」用后端算好的 can_book（口径与 create_appointment 的校验一致）。
 */
async function loadSchedules() {
  try {
    const res = await list_course_schedules({
      course_type: queryForm.course_type || undefined,
      keyword: queryForm.keyword || undefined
    });
    scheduleList.value = res.data || [];
  } catch (err) {
    toast.show(err.friendlyMessage || "加载排课失败", "error");
  }
}

// tab切换 后端course_type：group团课，private私教
function handleTabChange(tab) {
  activeTab.value = tab;
  queryForm.page = 1;
  if (tab === 'group') {
    queryForm.course_type = 'group';
  } else if (tab === 'private') {
    queryForm.course_type = 'private'; //修复原来多余空格 bug
  } else {
    queryForm.course_type = '';
  }
  loadData();
}

// 分页
function prevPage() {
  if (queryForm.page > 1) {
    queryForm.page -= 1;
    loadData();
  }
}
function nextPage() {
  queryForm.page += 1;
  loadData();
}

// 重置搜索
function resetSearch() {
  queryForm.keyword = "";
  queryForm.page = 1;
  loadData();
}

// 打开新增
function openAdd() {
  isEdit.value = false;
  editCourseId.value = null;
  const form = courseForm.value;
  form.name = "";
  form.coach_id = null;
  form.duration = null;
  form.price = null;
  form.category = null;
  form.course_type = activeTab.value === "group" ? 'group' : 'private';
  form.max_count = null;
  form.capacity = null;
  form.status = "已上架";
  form.start_time = null;
  form.location = "";
  showAdd.value = true;
}

// =========打开编辑：回填行数据==========
function openEdit(rowItem) {
  isEdit.value = true;
  editCourseId.value = rowItem.id;
  // 回填后端返回全部字段
  courseForm.value = {
    name: rowItem.name,
    course_type: rowItem.course_type,
    category: rowItem.category,
    location: rowItem.location || "",
    coach_id: rowItem.coach_id,
    duration: rowItem.duration,
    max_count: rowItem.max_count,
    // 之前漏了 capacity：编辑一次，私教名额就被 Number(undefined) 冲成 null
    capacity: rowItem.capacity,
    price: rowItem.price,
    status: rowItem.status,
    // datetime-local 只认 "2026-09-21T18:00"。
    // 列表里的 start_time 是「周六 08:01」这种展示串，回填进去输入框是空的，
    // 再保存就把展示串发给后端 → 解析失败或写坏数据
    start_time: rowItem.start_time_raw || ""
  };
  showAdd.value = true;
}

/** <input type="datetime-local"> 的 "2026-09-21T18:00" → 后端要的 "2026-09-21 18:00:00" */
function toBackendTime(value) {
  if (!value) return null;
  const normalized = String(value).replace("T", " ");
  return normalized.length === 16 ? `${normalized}:00` : normalized;
}

/** 数字输入框清空时是 ""，Number("") 会变成 0 把后端数据冲掉，这里统一转成 null */
function toNumberOrNull(value) {
  if (value === null || value === undefined || value === "") return null;
  const num = Number(value);
  return Number.isNaN(num) ? null : num;
}

/**
 * 加载授课教练下拉选项。
 * 会员没有教练管理权限（后端 /coaches 只放行 admin/reception/coach），
 * 所以只在能管课程的角色下才请求，避免会员进页面就弹一条 403 提示。
 */
async function loadCoaches() {
  if (!canManage.value) return;
  try {
    const res = await getCoachList({ page: 1, page_size: 100 });
    coachOptions.value = res.data?.items || [];
  } catch (err) {
    toast.show(err.friendlyMessage || "加载教练列表失败", "error");
  }
}

// 保存：新增 OR 更新
async function saveCourse() {
  const editing = isEdit.value;
  try {
    const form = courseForm.value;
    if (!form.coach_id) {
      toast.show("请选择授课教练", "error");
      return;
    }
    const submitData = {
      name: form.name,
      course_type: form.course_type,
      category: form.category,
      // 地点交给后端归一化：空白串会被存成 null（教练排课派生时据此跳过）
      location: form.location,
      coach_id: toNumberOrNull(form.coach_id),
      // 新增和编辑都要转：原来只有新增那一支做了格式化
      start_time: toBackendTime(form.start_time),
      duration: toNumberOrNull(form.duration),
      max_count: toNumberOrNull(form.max_count),
      capacity: toNumberOrNull(form.capacity),
      price: toNumberOrNull(form.price),
      status: form.status
    };

    if (editing) {
      // 编辑模式 PATCH 更新
      await update_courses(editCourseId.value,submitData);
      toast.show("课程已更新");
    } else {
      // 新增模式 POST
      await create_courses(submitData);
      toast.show("课程已新增");
    }
    await loadData();
    showAdd.value = false;

    //清空表单
    courseForm.value = {
      name: "",
      course_type: null,
      category: null,
      location: "",
      coach_id: null,
      start_time: null,
      duration: null,
      max_count: null,
      capacity: null,
      price: null,
      status: "已上架"
    };
  } catch (e) {
    toast.show(e.friendlyMessage || (editing ? "更新失败" : "新增失败"), "error");
  }
}

async function toggle(item) {
  try {
    const newStatus = item.status === "已下架" ? "已上架" : "已下架";
    await toggle_courses(item.id, { status: newStatus });
    toast.show(item.name + newStatus);
    loadData();
  } catch (err) {
    toast.show(err.friendlyMessage || "状态修改失败", "error");
  }
}

async function remove(item) {
  // 删课前先确认：课程一删，关联的排课和会员预约会一起没，
  // 且原来这里是「点一下就删」，没有二次确认。
  const ok = await confirmDialog({
    title: "删除课程",
    tone: "danger",
    message: "删除后该课程的排课与会员预约会一并消失，此操作不可恢复。",
    details: [
      { label: "课程", value: item.name },
      { label: "教练", value: item.coach_name || "—" }
    ],
    confirmText: "删除"
  });
  if (!ok) return;
  try {
    await delete_courses(item.id);
    toast.show("课程已删除");
    loadData();
  } catch (err) {
    // 课程还有预约时后端会拦下来并说明原因，这里要把原因透出来
    toast.show(err.friendlyMessage || "删除失败", "error");
  }
}

async function openReservation(item) {
  selectedCourse.value = item;
  showReservation.value = true;
  await get_appointments()
}
async function get_appointments(){
  const res = await get_course_appointments(selectedCourse.value.id);
  reservationList.value=res.data.items
}

/**
 * 会员预约某一次排课。
 *
 * 原来这里是 `book(item)`：直接拿课程表里的 start_time_raw 当预约时间发出去。
 * 那是课程的时间模板（可能是几周前甚至上个月的时间点），约出来的记录
 * 既对不上任何一次真实排课，也不会出现在教练的课表里。
 * 现在按排课的「日期 + 开始时间」下单，后端会把它关联到那条排课（schedule_id），
 * 之后教练改时间/地点，会员的预约视图跟着更新。
 */
async function bookSchedule(item) {
  const courseName = item.course_name || "该课程";
  const when = `${item.schedule_date} ${formatClock(item.start_time)}`;
  // 用应用内确认框代替原生 confirm：课程 / 时间 / 地点能排成清单，
  // 用户在点确定之前能一眼核对是不是自己要约的那一节。
  const ok = await confirmDialog({
    title: "确认预约",
    message: "预约后如需变更，请在「我的预约」里取消。",
    details: [
      { label: "课程", value: courseName },
      { label: "时间", value: when },
      { label: "地点", value: item.location || "待定" }
    ],
    confirmText: "确认预约"
  });
  if (!ok) {
    return;
  }
  try {
    await create_appointment({
      // 后端对会员角色会强制使用本人的会员档案，这里传自己的会员编号即可
      member_id: toNumberOrNull(useStore.role_id) ?? 0,
      course_id: item.course_id,
      appointment_time: `${item.schedule_date} ${item.start_time}`
    });
    toast.show(`预约成功：${courseName} ${when}`);
    await loadSchedules();
  } catch (err) {
    toast.show(err.friendlyMessage || "预约失败", "error");
  }
}


onMounted(async () => {
  await loadCoaches();
  await loadLocations();
  await loadData();
});
</script>
