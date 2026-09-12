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
          placeholder="选择预约日期"
          style="padding:6px 8px;width:200px;"
        />
        <button class="btn btn-primary" @click="loadData">搜索</button>
        <button class="btn btn-secondary" @click="resetSearch">重置</button>
        <!-- ✅ 新增预约按钮：只有管理员、前台可以看到 -->

      </div>

      <div class="tabs">
        <button class="tab-btn" :class="{ active: activeTab === 'all' }" type="button" @click="handleTabChange('all')">全部预约</button>
        <button class="tab-btn" :class="{ active: activeTab === 'reserved' }" type="button" @click="handleTabChange('已预约')">已预约</button>
        <button class="tab-btn" :class="{ active: activeTab === 'checked' }" type="button" @click="handleTabChange('已签到')">已签到</button>
        <button class="tab-btn" :class="{ active: activeTab === 'canceled' }" type="button" @click="handleTabChange('已取消')">已取消</button>
      </div>

      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>预约ID</th>
                <th>课程名称</th>
                <th>授课教练</th>
                <th>预约时间</th>
                <th>预约状态</th>
                <th>备注</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in currentList" :key="item.id">
                <td>{{ item.id }}</td>
                <td>{{ item.course }}</td>
                <td>{{ item.coach || '-' }}</td>
                <td>{{ item.appointment_time }}</td>
                <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
                <td>{{ item.remark || '-' }}</td>
                <td>
                  <div class="page-actions">
                    <!-- 签到：仅已预约状态可签到，教练/前台权限 -->
                    <button v-if="canManage && item.status === '已预约'" class="btn btn-primary btn-sm" type="button" @click="handleCheckin(item)">签到</button>
                    <!-- 取消预约：仅已预约状态，会员/前台/管理员 -->
                    <button v-if="(canManage || role === 'member') && item.status === '已预约'" class="btn btn-danger btn-sm" type="button" @click="handleCancel(item)">取消预约</button>
                    <!-- 冲突处理：管理员/前台 -->
                    <button v-if="isAdminOrReception && item.status === '已预约'" class="btn btn-secondary btn-sm" type="button" @click="openResolve(item)">冲突处理</button>
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
          <div class="field">
            <label>状态</label>
            <select v-model="resolveForm.status">
              <option value="已预约">已预约</option>
              <option value="已取消">已取消</option>
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

    <!-- ✅ 新增预约弹窗 -->
    <div v-if="showCreate" class="modal-mask" @click.self="showCreate = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">新增预约</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showCreate = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="field">
            <label>会员ID</label>
            <input v-model="createForm.member_id" type="number" placeholder="输入会员ID"/>
          </div>
          <div class="field">
            <label>课程ID</label>
            <input v-model="createForm.course_id" type="number" placeholder="输入课程ID"/>
          </div>
          <div class="field">
            <label>预约时间</label>
            <input v-model="createForm.appointment_time" type="datetime-local"/>
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
import {useAuth} from "../composables/useAuth";
import {useToast} from "../composables/useToast";
import {
  list_appointments,
  checkin_appointment,
  create_appointment,
  cancel_appointment,
  resolve_appointment
} from "../api/appointments.js";
import {useUserStore} from "../stores/user.js";

const useStore = useUserStore();
const auth = useAuth();
const toast = useToast();
const role = useStore.role;

// 权限
const canManage = role === "admin" || role === "reception" || role === "coach";
const isAdminOrReception = role === "admin" || role === "reception";

const activeTab = ref("all");
const showResolve = ref(false);
const showCreate = ref(false); // ✅ 新增弹窗开关
const selectedAppointment = ref(null);

// 查询参数
const queryForm = reactive({
  keyword: null,
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

// ✅ 新增预约表单
const createForm = ref({
  member_id: null,
  course_id: null,
  appointment_time: "",
});

const pageTitle = computed(() => {
  if (role === "member") return "我的预约";
  return "预约管理";
});
const pageDesc = computed(() => {
  if (role === "member") return "查看我的课程预约，可取消未开始预约";
  return "管理会员课程预约、签到、预约冲突处理";
});

// 状态样式
function statusClass(status) {
  if (status === "已预约") return "info";
  if (status === "已签到") return "success";
  if (status === "已取消") return "muted";
  return "";
}

// 加载预约列表
async function loadData() {
  try {
    const params = {...queryForm};
    console.log(queryForm)
    Object.keys(params).forEach(k => {
      if (params[k] === "") params[k] = undefined;
    });
    const res = await list_appointments(params);
    console.log(res)
    tableData.value = res.data.items;
    total.value = res.data.total;
  } catch (err) {
    toast.show("加载预约列表失败", "error");
    console.error(err);
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

// 签到
async function handleCheckin(item) {
  try {
    await checkin_appointment(item.id);
    toast.show("签到成功");
    await loadData();
  } catch (err) {
    toast.show("签到失败", "error");
  }
}

// 取消预约
async function handleCancel(item) {
  try {
    await cancel_appointment(item.id);
    toast.show("预约已取消");
    await loadData();
  } catch (err) {
    toast.show("取消预约失败", "error");
  }
}

// 打开冲突处理弹窗
function openResolve(item) {
  selectedAppointment.value = item;
  resolveForm.value.status = item.status;
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
    loadData();
  } catch (err) {
    toast.show("更新失败", "error");
  }
}

// ✅ 打开新增预约弹窗，清空表单
function openCreateModal() {
  createForm.value = {
    member_id: null,
    course_id: null,
    appointment_time: "",
  };
  showCreate.value = true;
}

// ✅ 提交新增预约
async function submitCreate() {
  if (!createForm.value.member_id || !createForm.value.course_id || !createForm.value.appointment_time) {
    toast.show("会员ID、课程ID、预约时间不能为空", "error");
    return;
  }
  try {
    // ✅ 补全秒数，转成 "2026-09-12 19:00:00" 标准格式
    const timeStr = createForm.value.appointment_time.replace("T", " ") + ":00";
    const payload = {
      member_id: Number(createForm.value.member_id),
      course_id: Number(createForm.value.course_id),
      appointment_time: timeStr,
      remark: createForm.value.remark || ""
    };
    console.log(createForm.value)
    await create_appointment(payload);
    toast.show("新增预约成功");
    showCreate.value = false;
    loadData();
  } catch (err) {
    // ✅ 把后端返回的具体错误提示给用户
    const msg = err.response?.data?.detail || "新增预约失败";
    toast.show(msg, "error");
  }
}

onMounted(async () => {
  await loadData();
});
</script>

<style scoped>

</style>