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
        <button class="tab-btn" :class="{ active: activeTab === 'all' }" type="button" @click="handleTabChange('all')">所有课程</button>
        <button class="tab-btn" :class="{ active: activeTab === 'group' }" type="button" @click="handleTabChange('group')">公共团课</button>
        <button class="tab-btn" :class="{ active: activeTab === 'private' }" type="button" @click="handleTabChange('private')">私教课程</button>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>课程名称</th>
                <th>分类</th>
                <th>授课教练</th>
                <th>课时时长</th>
                <th>上课时间</th>
                <th>课时单价</th>
                <th>人数</th>
                <th>持续时长</th>
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
                <td>¥ {{ item.price }}</td>
                <!-- 团课显示人数，私教显示- -->
                <td>{{ item.max_count }}</td>
                <!-- 私教显示会员名额，团课显示- -->
                <td>{{ item.duration }}</td>
                <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
                <td>
                  <div class="page-actions">
                    <button v-if="canManage" class="btn btn-secondary btn-sm" type="button" @click="toggle(item)">
                      {{ item.status === '已下架' ? '上架' : '下架' }}
                    </button>
                    <button v-if="canManage" class="btn btn-danger btn-sm" type="button" @click="remove(item)">删除</button>
                    <button v-if="!canManage && role === 'coach'" class="btn btn-secondary btn-sm" type="button" @click="openReservation(item)">预约名单</button>
                    <button v-if="!canManage && role === 'member'" class="btn btn-primary btn-sm" type="button" @click="book(item)">预约</button>
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

    <div v-if="showAdd" class="modal-mask" @click.self="showAdd = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">新增课程</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showAdd = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field full"><label>课程名称</label><input v-model="courseForm.name" type="text"></div>
            <div class="field"><label>授课教练ID</label><input v-model.number="courseForm.coach_id" type="number"></div>
            <div class="field"><label>课程类型</label><input v-model="courseForm.category" type="text"></div>
            <div class="field"><label>时长(分钟)</label><input v-model.number="courseForm.duration" type="number"></div>
            <div class="field"><label>价格</label><input v-model.number="courseForm.price" type="number"></div>
            <div class="field"><label>课程类型(1团课/2私教)</label><input v-model="courseForm.course_type" type="text"></div>
            <div class="field"><label>最大人数</label><input v-model.number="courseForm.max_count" type="number"></div>
            <div class="field"><label>状态</label>
              <select v-model="courseForm.status">
                <option>已上架</option>
                <option>已下架</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showAdd = false">取消</button>
          <button class="btn btn-primary" type="button" @click="saveCourse">保存</button>
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
                <tr><th>会员</th><th>手机号</th><th>状态</th></tr>
              </thead>
              <tbody>
                <tr v-for="item in reservationList" :key="item.member">
                  <td>{{ item.member }}</td>
                  <td>{{ item.phone }}</td>
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
import {create_courses, list_courses} from "../api/courses.js";
import {useUserStore} from "../stores/user.js";
const useStore = useUserStore();
const auth = useAuth();
const toast = useToast();
const role = useStore.role;
const canManage = role === "admin" || role === "reception";

const activeTab = ref("all");
const showAdd = ref(false);
const showReservation = ref(false);
const selectedCourse = ref(null);

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

// 新增表单
const courseForm = ref({
  name: "",
  course_type: null,
  category:null,
  coach_id: null,
  start_time:null,
  duration: null,
  max_count: null,
  price: null,
  status: "已上架"
});

const total = ref(0);
const tableData = ref([]);

// 当前页面列表
const currentList = computed(() => tableData.value);

const reservationList = computed(() => {
  if (!selectedCourse.value) return [];
  return [
    { member: "王琳", phone: "13800000001", status: "已预约" },
    { member: "赵敏", phone: "13800000003", status: "已预约" },
    { member: "郑雪", phone: "13800000011", status: "已签到" }
  ];
});

const pageTitle = computed(() => {
  if (role === "reception") return "预约处理";
  if (role === "coach") return "课程中心";
  if (role === "member") return "预约课程";
  return "课程与预约";
});

const pageDesc = computed(() => {
  if (role === "member") return "浏览可预约课程并管理自己的预约。";
  if (role === "coach") return "查看课程信息、预约人数和授课安排。";
  if (role === "reception") return "处理课程预约、取消预约和会员签到。";
  return "维护公共团课、私教课程和会员预约记录。";
});

function statusClass(status) {
  if (status === "已上架") return "success";
  if (status === "已满员") return "warn";
  return "muted";
}

// 加载后端分页列表
async function loadData() {
  try {
    // get查询参数
    const params = { ...queryForm };
    // 空字符串转undefined，避免传给后端空字符串过滤
    Object.keys(params).forEach(k => {
      if (params[k] === "") params[k] = undefined;
    });
    const res = await list_courses(params);
    console.log(res);
    tableData.value = res.data.items;
    total.value = res.data.total;
  } catch (err) {
    toast.show("加载课程列表失败", "error");
    console.error(err);
  }
}

// tab切换 后端course_type：1团课，2私教
function handleTabChange(tab) {
  activeTab.value = tab;
  queryForm.page = 1;
  if(tab === 'group'){
    queryForm.course_type = 'group';
  }else if(tab === 'private'){
    queryForm.course_type = 'private ';
  }else{
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

function openAdd() {
  // 修复：ref必须 .value 访问内部对象
  const form = courseForm.value;
  form.name = "";
  form.coach_id = null;
  form.duration = null;
  form.price = null;
  form.category = null;
  form.course_type = activeTab.value === "group" ? 'group' :'private';
  form.max_count = null;
  form.status = "已上架";
  form.start_time = null;
  showAdd.value = true;
}

// 保存新增课程，调用后端post接口
async function saveCourse() {
  try {
    const form = courseForm.value;
    // 组装纯净普通对象，脱离reactive代理，严格匹配OpenAPI schema
    const submitData = {
      name: form.name,
      course_type: form.course_type, // 字符串 "1" / "2"
      category: form.category,       // 字符串
      coach_id: Number(form.coach_id),
      duration: Number(form.duration),
      max_count: Number(form.max_count),
      price: Number(form.price),
      start_time: new Date().toISOString(), // 带Z标准UTC时间
      status: form.status
    };

    console.log("提交数据", submitData);
    // ✅ 传纯净对象，不要传ref、不要传ref.value代理对象
    let res = await create_courses(submitData);
    console.log(res);

    showAdd.value = false;
    toast.show("课程已新增");
    loadData();

    // 重置表单
    courseForm.value = {
      name: "",
      course_type: null,
      category: null,
      coach_id: null,
      start_time: null,
      duration: null,
      max_count: null,
      price: null,
      status: "已上架"
    };
  } catch (e) {
    console.error(e);
    toast.show("新增失败", "error");
  }
}

async function toggle(item) {
  try {
    const newStatus = item.status === "已下架" ? "已上架" : "已下架";
    await request.patch(`/api/v1/courses/${item.id}`, { status: newStatus });
    toast.show(item.name + " 已" + newStatus);
    loadData();
  } catch {
    toast.show("状态修改失败","error");
  }
}

async function remove(item) {
  try {
    await request.delete(`/api/v1/courses/${item.id}`);
    toast.show("课程已删除");
    loadData();
  } catch {
    toast.show("删除失败","error");
  }
}

function openReservation(item) {
  selectedCourse.value = item;
  showReservation.value = true;
}

function book(item) {
  toast.show("预约成功，可在会员个人中心查看");
}

onMounted(() => {
  loadData();
  console.log(auth.currentRole.value)
});
</script>