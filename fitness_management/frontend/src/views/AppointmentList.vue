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
       <button v-if="isAdminOrReception" class="btn btn-primary" @click="openCreateModal">新增预约</button>
    </div>

    <div class="panel">
      <!-- 搜索栏 -->
      <div class="panel-search" style="display:flex;gap:12px;align-items:center;padding:16px;">
        <input
          v-model="queryForm.keyword"
          type="text"
          placeholder="输入会员姓名/课程名称搜索"
          style="padding:6px 8px;width:260px;"
          @keyup.enter="loadData"
        />
        <input
          v-model="queryForm.date"
          type="date"
          placeholder="按上课日期筛选"
          style="padding:6px 8px;width:200px;"
        />
        <button class="btn btn-primary" @click="loadData">搜索</button>
        <button class="btn btn-secondary" @click="resetSearch">重置</button>
      </div>

      <div class="tabs">
        <!-- tab 的 key 直接复用后端状态值。原来按钮传的是「已预约」而高亮判断写的是
             'reserved'，两边对不上，任何 tab 都不会高亮 -->
        <button class="tab-btn" :class="{ active: activeTab === 'all' }" type="button" @click="handleTabChange('all')">全部预约</button>
        <button class="tab-btn" :class="{ active: activeTab === '待预约' }" type="button" @click="handleTabChange('待预约')">待预约</button>
        <button class="tab-btn" :class="{ active: activeTab === '已预约' }" type="button" @click="handleTabChange('已预约')">已预约</button>
        <button class="tab-btn" :class="{ active: activeTab === '已签到' }" type="button" @click="handleTabChange('已签到')">已签到</button>
        <button class="tab-btn" :class="{ active: activeTab === '已取消' }" type="button" @click="handleTabChange('已取消')">已取消</button>
      </div>

      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>预约ID</th>
                <th>会员</th>
                <th>课程名称</th>
                <th>授课教练</th>
                <th>上课时间</th>
                <th>上课地点</th>
                <th>预约状态</th>
                <th>排课状态</th>
                <th>备注</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!currentList.length">
                <td colspan="10" style="text-align:center;color:#999;">暂无预约记录</td>
              </tr>
              <tr v-for="item in currentList" :key="item.id">
                <td>{{ item.id }}</td>
                <td>{{ item.member || '-' }}<span v-if="item.phone" style="color:#999;"> · {{ item.phone }}</span></td>
                <!-- 课时费就摆在课程旁边：签到是按这个价从会员余额里扣的，
                     点之前要让操作的人看见要扣多少 -->
                <td>
                  {{ item.course }}
                  <span v-if="item.course_price" style="color:#999;font-size:12px;"> · 课时费 ¥{{ item.course_price }}</span>
                </td>
                <td>{{ item.coach || '-' }}</td>
                <td>{{ classTimeOf(item) }}</td>
                <td>{{ item.schedule_location || '-' }}</td>
                <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
                <td><span class="badge" :class="scheduleStatusClass(item.schedule_status)">{{ item.schedule_status || '—' }}</span></td>
                <td>{{ item.remark || '-' }}</td>
                <td>
                  <div class="page-actions">
                    <!-- 签到：前台/教练/管理员给未签到的预约签到；会员只能给自己签，
                         且只在上课时段内（can_checkin 由后端按排课时间算好下发） -->
                    <button v-if="showCheckin(item)" class="btn btn-primary btn-sm" type="button" @click="handleCheckin(item)">签到</button>
                    <!-- 取消预约：未签到状态下会员/前台/管理员均可；会员侧还要课没上完 -->
                    <button v-if="showCancel(item)" class="btn btn-danger btn-sm" type="button" @click="handleCancel(item)">取消预约</button>
                    <!-- 冲突处理：只有「待预约」才出现。它是时段撞车留下的待办，
                         其余状态都是已经定了的事，不该再挂一个「处理冲突」入口 -->
                    <button v-if="isAdminOrReception && isConflictPending(item.status)" class="btn btn-secondary btn-sm" type="button" @click="openResolve(item)">冲突处理</button>
                    <span v-if="!showCheckin(item) && !showCancel(item) && !(isAdminOrReception && isConflictPending(item.status))" style="color:#999;">-</span>
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

    <!-- 冲突处理弹窗 -->
    <div v-if="showResolve" class="modal-mask" @click.self="showResolve = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">预约冲突处理</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showResolve = false">关闭</button>
        </div>
        <div class="modal-body">
          <p class="field-hint" style="margin-bottom:10px;">
            该会员在这个时段已有其他预约。保留则转为「已预约」并占用课程名额，取消则不占名额。
          </p>
          <div class="field">
            <label>状态</label>
            <select v-model="resolveForm.status">
              <option value="已预约">已预约（保留这一单）</option>
              <option value="已取消">已取消（退掉这一单）</option>
            </select>
          </div>
          <div class="field">
            <label>备注</label>
            <textarea v-model="resolveForm.remark" rows="4" placeholder="填写冲突处理备注"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showResolve = false">取消</button>
          <button class="btn btn-primary" type="button" @click="submitResolve">提交</button>
        </div>
      </div>
    </div>

    <!-- 新增预约弹窗 -->
    <div v-if="showCreate" class="modal-mask" @click.self="showCreate = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">新增预约</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showCreate = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="field">
            <!-- 原来是手填「会员ID」，得先知道库里的编号才能预约。改成从会员接口拉数据渲染下拉框。 -->
            <label>会员</label>
            <select v-model.number="createForm.member_id">
              <option :value="null" disabled>请选择会员</option>
              <option v-for="m in memberOptions" :key="m.id" :value="m.id">{{ memberLabel(m) }}</option>
            </select>
          </div>
          <div class="field">
            <!-- 同理：课程也改成下拉框，并且选中后自动带出该课程的上课时间 -->
            <label>课程</label>
            <select v-model.number="createForm.course_id" @change="onCourseChange">
              <option :value="null" disabled>请选择课程</option>
              <option v-for="c in courseOptions" :key="c.id" :value="c.id">{{ courseLabel(c) }}</option>
            </select>
          </div>
          <div class="field">
            <label>预约时间</label>
            <input v-model="createForm.appointment_time" type="datetime-local"/>
            <p v-if="selectedCourseTime" class="field-hint">已按课程排课时间自动填入，可微调</p>
          </div>

        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showCreate = false">取消</button>
          <button class="btn btn-primary" type="button" @click="submitCreate">提交新增</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {computed, reactive, ref, onMounted} from "vue";
import {useToast} from "../composables/useToast";
import {confirmDialog} from "../composables/useConfirm.js";
import {
  list_appointments,
  checkin_appointment,
  create_appointment,
  cancel_appointment,
  resolve_appointment
} from "../api/appointments.js";
import {useUserStore} from "../stores/user.js";
import {getMemberList} from "../api/member.js";
import {checkinMyAppointment} from "../api/member-center.js";
import {list_courses} from "../api/courses.js";
import {isConflictPending, isUnchecked, canCheckin, canCancel, BOOKED, statusClass, scheduleStatusClass} from "../utils/appointmentStatus.js";

const useStore = useUserStore();
const toast = useToast();
// 用 computed：解构出来的 role 是一次性快照，同页切换身份不会跟着更新
const role = computed(() => useStore.role);

// 权限
const canManage = computed(() => ["admin", "reception", "coach"].includes(role.value));
const isAdminOrReception = computed(() => role.value === "admin" || role.value === "reception");

/**
 * 行内按钮的显示条件，前台/教练/管理员和会员两套口径：
 *
 *  · 工作人员是管理动作 —— 只要是正常「已预约」就给按钮，不受上课时段限制
 *    （补签、纠错都要能操作）；但「待预约」不行 —— 它连名额都没占，
 *    得先在处理冲突里定下来；
 *  · 会员是自助动作 —— 签到只能在上课时段内（can_checkin），
 *    取消只能在这节课还没上完、也没签过到的时候（can_cancel）。
 *    两个标记都由后端按排课时间算好下发，前端不再自己判一遍。
 */
const showCheckin = (item) =>
  canManage.value ? item.status === BOOKED : canCheckin(item);

const showCancel = (item) =>
  canManage.value ? isUnchecked(item.status) : canCancel(item);

const activeTab = ref("all");
const showResolve = ref(false);
const showCreate = ref(false);
const selectedAppointment = ref(null);

// 查询参数
const queryForm = reactive({
  keyword: "",
  date: "",
  status: "",
  page: 1,
  page_size: 10
});

const total = ref(0);
const tableData = ref([]);
const currentList = computed(() => tableData.value);

// 冲突处理表单
const resolveForm = ref({
  status: "已预约",
  remark: ""
});

// 新增预约表单
const createForm = ref({
  member_id: null,
  course_id: null,
  appointment_time: "",
});

// 下拉框数据源：会员、课程都从各自接口拉真实数据，不让用户手输编号
const memberOptions = ref([]);
const courseOptions = ref([]);

/** 下拉框显示文案：把「姓名 · 手机号」拼好，避免在 <option> 里嵌套条件模板 */
function memberLabel(member) {
  return member.phone ? `${member.name} · ${member.phone}` : member.name;
}

function courseLabel(course) {
  return course.coach_name ? `${course.name} · ${course.coach_name}` : course.name;
}

/** 当前选中课程在库里的排课时间（datetime-local 格式），用于提示是否已自动填入 */
const selectedCourseTime = computed(() => {
  const course = courseOptions.value.find(c => c.id === createForm.value.course_id);
  return course?.start_time_raw || "";
});

const pageTitle = computed(() => {
  if (role.value === "member") return "我的预约";
  return "预约管理";
});
const pageDesc = computed(() => {
  if (role.value === "member") return "查看我的课程预约，可取消未开始预约";
  return "管理会员课程预约、签到、预约冲突处理";
});

// 状态样式统一放在 utils/appointmentStatus.js，避免多个页面各写一套、状态值还对不上

/**
 * 预约的「上课时间」。
 *
 * 优先取排课的最新日期 + 时段 —— 教练把这一次课挪到别的日子/时段后，
 * 这里显示的就是新时间；关联不到排课（窗口外的历史预约）才退回预约快照
 * appointment_time。口径与会员中心「我的预约」保持一致，两端不会各说各的。
 */
function classTimeOf(item) {
  if (!item) return "-";
  if (item.schedule_date) {
    const start = item.schedule_start ?? "";
    const end = item.schedule_end ? `~${item.schedule_end}` : "";
    return `${item.schedule_date} ${start}${end}`.trim() || "-";
  }
  return item.appointment_time || "-";
}

// 加载预约列表
async function loadData() {
  try {
    // 空字符串要在发请求前剔掉，否则会被当成有效的筛选条件
    const params = {};
    Object.keys(queryForm).forEach(k => {
      if (queryForm[k] !== "") params[k] = queryForm[k];
    });
    const res = await list_appointments(params);
    tableData.value = res.data.items;
    total.value = res.data.total;
  } catch (err) {
    toast.show(err.friendlyMessage || "加载预约列表失败", "error");
  }
}

// tab切换
function handleTabChange(tab) {
  activeTab.value = tab;
  queryForm.page = 1;
  if (tab === "all") {
    queryForm.status = "";
  } else {
    queryForm.status = tab;
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
async function resetSearch() {
  queryForm.keyword = "";
  queryForm.date = "";
  queryForm.status = "";
  queryForm.page = 1;
  await loadData();
}

// 签到。会员走 /member_center 的自助签到（多一道上课时段的闸），
// 其余角色走 /appointments 的代签入口 —— 两条路径的越权口径不一样，
// 但扣款一致：状态一落到「已签到」就按课程当前课时费从会员余额里出。
async function handleCheckin(item) {
  try {
    const res = role.value === "member"
      ? await checkinMyAppointment(item.id)
      : await checkin_appointment(item.id);
    // 签到即扣款（代签也一样），把扣了多少、还剩多少直接说清楚
    toast.show(res.data?.charged ? `签到成功，已扣课时费 ${res.data.charged} 元，余额 ${res.data.balance} 元` : "签到成功");
    await loadData();
  } catch (err) {
    toast.show(err.friendlyMessage || "签到失败", "error");
  }
}

// 取消预约
async function handleCancel(item) {
  // 取消预约原来没有确认，管理端一点就退掉会员的预约，容易误操作
  const ok = await confirmDialog({
    title: "取消预约",
    tone: "danger",
    message: "取消后该预约席位会被释放，如需上课请重新预约。",
    details: [
      { label: "会员", value: item.member || "—" },
      { label: "课程", value: item.course || "—" },
      { label: "时间", value: classTimeOf(item) }
    ],
    confirmText: "取消预约"
  });
  if (!ok) return;
  try {
    await cancel_appointment(item.id);
    toast.show("预约已取消");
    await loadData();
  } catch (err) {
    toast.show(err.friendlyMessage || "取消预约失败", "error");
  }
}

// 打开冲突处理弹窗。目标状态默认给「已预约」（保留这一单），
// 不回填 item.status —— 它此刻是「待预约」，不是合法的目标状态。
function openResolve(item) {
  selectedAppointment.value = item;
  resolveForm.value.status = "已预约";
  resolveForm.value.remark = item.remark || "";
  showResolve.value = true;
}

// 提交冲突处理
async function submitResolve() {
  try {
    await resolve_appointment(selectedAppointment.value.id, {
      status: resolveForm.value.status,
      remark: resolveForm.value.remark
    });
    toast.show("预约信息已更新");
    showResolve.value = false;
    await loadData();
  } catch (err) {
    toast.show(err.friendlyMessage || "更新失败", "error");
  }
}

/** 拉取下拉框数据（会员 / 课程）。只有 admin、reception 能打开这个弹窗，对应后端也放行这两个角色 */
async function loadOptions() {
  try {
    const [memberRes, courseRes] = await Promise.all([
      getMemberList({ page: 1, page_size: 100 }),
      list_courses({ page: 1, page_size: 100 })
    ]);
    memberOptions.value = memberRes.data?.items || [];
    courseOptions.value = courseRes.data?.items || [];
  } catch (err) {
    toast.show(err.friendlyMessage || "加载会员/课程列表失败", "error");
  }
}

/** 选中课程后把上课时间自动带出来，避免手填一个跟课程对不上的时段 */
function onCourseChange(courseId) {
  const course = courseOptions.value.find(c => c.id === courseId);
  if (course?.start_time_raw) {
    createForm.value.appointment_time = course.start_time_raw;
  }
}

// 打开新增预约弹窗，清空表单并加载下拉选项
function openCreateModal() {
  createForm.value = {
    member_id: null,
    course_id: null,
    appointment_time: ""
  };
  showCreate.value = true;
  loadOptions();
}

// 提交新增预约
async function submitCreate() {
  if (!createForm.value.member_id || !createForm.value.course_id || !createForm.value.appointment_time) {
    toast.show("请选择会员、课程并填写预约时间", "error");
    return;
  }
  try {
    // <input type="datetime-local"> 给的是 2026-09-12T19:00，补上秒数才符合后端格式
    const timeStr = createForm.value.appointment_time.replace("T", " ") + ":00";
    await create_appointment({
      member_id: Number(createForm.value.member_id),
      course_id: Number(createForm.value.course_id),
      appointment_time: timeStr
    });
    toast.show("新增预约成功");
    showCreate.value = false;
    await loadData();
  } catch (err) {
    toast.show(err.friendlyMessage || "新增预约失败", "error");
  }
}

onMounted(async () => {
  await loadData();
});
</script>

<style scoped>

</style>