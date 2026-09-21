<template>
  <div>
    <div class="page-header">
      <div>
        <h1>教练管理</h1>
        <p class="page-desc">管理教练档案、专长排班与授课统计。</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary" @click="openAddCoach">新增教练</button>
      </div>
    </div>

    <div class="stat-grid">
      <!-- 传值一律用 :value：StatCard 没有 emit，写 v-model:value 只会在根元素上挂一个
           永远不会被触发的事件，看着像双向绑定其实不是 -->
      <StatCard label="在职教练" :value="stat_total_coach" unit="人" icon="人" />
      <StatCard label="今日排课" :value="stat_today_course" unit="节" icon="排" />
      <StatCard label="累计授课课时" :value="stat_sum_hours" unit="课时" icon="课" tone="warn" />
      <StatCard label="平均评分" :value="stat_avg_score" unit="分" icon="分" />
    </div>

   <div class="panel-search" style="display:flex;gap:12px;align-items:center;padding:16px;flex-wrap:wrap;">
  <input
    v-model="queryForm.keyword"
    type="text"
    placeholder="输入教练姓名/手机号搜索"
    style="padding:6px 8px;width:260px;"
  />
  <select v-model="queryForm.status" style="padding:6px 8px;">
    <option value="">全部状态</option>
    <option value="在职">在职</option>
    <option value="休假">休假</option>
    <option value="离职">离职</option>
  </select>
  <input
    v-model="queryForm.specialty"
    type="text"
    placeholder="专长筛选"
    style="padding:6px 8px;width:180px;"
  />
  <!-- 不需要搜索按钮，控件修改防抖自动请求，保留重置 -->
  <button class="btn btn-secondary" @click="resetSearch">重置</button>
</div>

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">教练列表</h2>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>姓名</th>
                <th>联系方式</th>
                <th>专长</th>
                <th>状态</th>
                <th>入职时间</th>
                <th>本月课时</th>
                <th>评分</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in list" :key="item.id">
                <td>{{ item.name }}</td>
                <td>{{ item.phone }}</td>
                <td>
                  <span class="tag" v-for="sp in item.specialties" :key="sp">{{ sp }}</span>
                </td>
                <td>
                  <span
                    class="badge"
                    :class="
                      item.status === '在职'
                        ? 'success'
                        : item.status === '休假'
                        ? 'warn'
                        : 'muted'
                    "
                  >
                    {{ item.status }}
                  </span>
                </td>
                <td>{{ item.hire_date }}</td>
                <td>{{ item.hours ?? 0 }}</td>
                <td>{{ item.score ?? 0 }}</td>
                <td>
                  <div class="page-actions">
                    <button class="btn btn-secondary btn-sm" @click="openCoachDetail(item)">统计详情</button>
                    <button class="btn btn-secondary btn-sm" @click="openEditCoach(item)">编辑</button>
                    <button class="btn btn-danger btn-sm" @click="handleDeleteCoach(item)">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <el-pagination
        v-model:current-page="queryForm.page"
        v-model:page-size="queryForm.page_size"
        size="large"
        background
        layout="prev, pager, next"
        :total="total"
        class="mt-4"
        @current-change="() => loadData()"
      />
    </div>

    <!-- 新增/编辑教练弹窗 -->
    <div v-if="showCoachModal" class="modal-mask" @click.self="showCoachModal = false">
      <div class="modal">
        <div class="modal-header">
      <h3 class="panel-title">{{ isEditCoach ? "编辑教练" : "新增教练" }}</h3>
      <button class="btn btn-secondary btn-sm" @click="closeCoachModal">关闭</button>
    </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field">
              <label>姓名</label>
              <input v-model="coachForm.name" type="text" />
            </div>
            <div class="field">
              <label>手机号</label>
              <input v-model="coachForm.phone" type="text" />
            </div>
            <div class="field">
              <label>专长（逗号分隔）</label>
              <input v-model="coachForm.specialties" type="text" placeholder="力量训练,增肌塑形" />
            </div>
            <div class="field">
              <label>薪资</label>
              <input v-model="coachForm.salary" type="number" placeholder="力量训练,增肌塑形" />
            </div>
            <div class="field">
              <label>入职时间</label>
              <input v-model="coachForm.hire_date" type="date" />
            </div>
            <div class="field">
              <label>课时</label>
              <input v-model.number="coachForm.hours" type="number" step="1"/>
            </div>
            <div class="field">
              <label>评分</label>
              <input v-model.number="coachForm.score" type="number" step="0.1"/>
            </div>
            <div class="field">
              <label>状态</label>
              <select v-model="coachForm.status">
                <option value="在职">在职</option>
                <option value="休假">休假</option>
                <option value="离职">离职</option>
              </select>
            </div>
          </div>
          <!-- 教练必须能登录才有意义：新增时会顺带开一个账号，
               凭据就是「手机号 + 123456」，当面告知本人即可。 -->
          <p v-if="!isEditCoach" class="field-hint">
            保存后会同时为该教练创建登录账号：账号为上面填写的手机号，初始密码 123456。
          </p>
        </div>
         <div class="modal-footer">
      <button class="btn btn-secondary" @click="closeCoachModal">取消</button>
      <button class="btn btn-primary" @click="saveCoach">{{ isEditCoach ? "保存修改" : "保存新增" }}</button>
    </div>
      </div>
    </div>

    <!-- 教练授课统计详情弹窗 9.5接口 -->
    <div v-if="showStatModal" class="modal-mask" @click.self="showStatModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">教练授课统计 - {{ statCoachInfo?.name }}</h3>
          <button class="btn btn-secondary btn-sm" @click="showStatModal = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field"><label>教练ID</label>{{ statData.coach_id }}</div>
            <div class="field"><label>累计授课课时</label>{{ statData.total_hours }}</div>
            <div class="field"><label>服务学员数</label>{{ statData.student_count }}</div>
            <div class="field"><label>平均评分</label>{{ statData.average_score }}</div>
            <div class="field"><label>累计营收</label>¥ {{ statData.revenue }}</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showStatModal = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import StatCard from "../components/StatCard.vue";
import { ElPagination } from "element-plus";
import { reactive, ref, onMounted, watch } from "vue";
import { getCoachList, addCoach, updateCoach, deleteCoach, getCoachStat } from "../api/coach";
import { list_course_schedules } from "../api/courses.js";
import { useToast } from "../composables/useToast";
import { confirmDialog } from "../composables/useConfirm.js";

const toast = useToast();

const queryForm = ref({
  page: 1,
  page_size: 10,
  keyword: "",
  status: "",
  specialty: ""
});

const list = ref([]);
const total = ref(0);
const summary= ref({});
const stat_total_coach = ref(0);
const stat_today_course = ref(0);
const stat_sum_hours = ref(0);
const stat_avg_score = ref(0);

const showCoachModal = ref(false);
const isEditCoach = ref(false);
const editCoachId = ref(null);
const coachForm = reactive({
  name: "",
  phone: "",
  specialties: '',
  salary:0,
  hire_date: "",
  hours:0,
  score:0,
  status: "在职",
});

// 🔹搜索栏防抖定时器
let searchDebounceTimer = null;
const SEARCH_DELAY = 450;

const showStatModal = ref(false);
const statCoachInfo = ref(null);
const statData = reactive({
  coach_id: 0,
  total_hours: 0,
  student_count: 0,
  average_score: 0,
  revenue: 0,
});

// ========== 搜索监听（保留，分页不会跳回第一页） ==========
watch(
  [() => queryForm.value.keyword, () => queryForm.value.status, () => queryForm.value.specialty],
  () => {
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      queryForm.value.page = 1;
      loadData();
    }, SEARCH_DELAY);
  }
);



// 关闭弹窗
function closeCoachModal() {
  showCoachModal.value = false;
}

function resetSearch(){
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
  queryForm.value.keyword = ""
  queryForm.value.status = ""
  queryForm.value.specialty = ""
  queryForm.value.page = 1
  loadData()
}

/**
 * 统计卡片：课时与评分取全部教练，不能只把「当前这一页」加起来 ——
 * 那样翻一页数字就跟着变，写在卡片上会被当成全馆口径。
 * 教练数量远小于 100，一次取全量即可。
 */
async function loadCoachesStat() {
  try {
    const res = await getCoachList({ page: 1, page_size: 100 });
    const all = res.data?.items || [];
    stat_total_coach.value = res.data?.total ?? all.length;
    stat_sum_hours.value = all.reduce((s, i) => s + (i.hours || 0), 0);
    const scoreArr = all.filter((i) => i.score);
    stat_avg_score.value = scoreArr.length
      ? Number((scoreArr.reduce((s, i) => s + i.score, 0) / scoreArr.length).toFixed(2))
      : 0;
  } catch (err) {
    console.warn("加载教练统计失败：", err?.friendlyMessage || err);
  }
}

/**
 * 今日排课：取全部教练在排课窗口内的课表，数出落在今天的节数。
 *
 * 原来这张卡片只有 ref(0) 从头到尾没人赋值 —— 无论哪天打开都显示 0 节。
 * 这里复用「全部教练排课」接口（返回今天起 4 周的课），只统计今天那一天。
 */
async function loadTodayScheduleCount() {
  try {
    const res = await list_course_schedules({});
    const today = todayLocal();
    stat_today_course.value = (res.data || []).filter((s) => s.schedule_date === today).length;
  } catch (err) {
    // 统计卡片取不到不影响教练列表本身，不打断页面
    console.warn("加载今日排课数失败：", err?.friendlyMessage || err);
  }
}

/** 本地日期 YYYY-MM-DD（不能用 toISOString，那是 UTC，晚上会差一天） */
function todayLocal() {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

async function loadData() {
  try {
    const res = await getCoachList(queryForm.value);
    list.value = res.data.items;
    total.value = res.data.total;
  } catch (e) {
    toast.show("加载教练列表失败");
  }
}

function openAddCoach() {
  isEditCoach.value = false;
  editCoachId.value = null;
  coachForm.name = "";
  coachForm.phone = "";
  coachForm.specialties = '';
  coachForm.status = "在职";
  coachForm.salary = 0
  coachForm.hire_date = new Date().toISOString().split("T")[0];
  // 课时与评分要归零：不重置的话，「先编辑 A、再新增 B」时 B 会带着 A 的课时和评分入职
  coachForm.hours = 0;
  coachForm.score = 5;
  showCoachModal.value = true;
}

function openEditCoach(item) {
  isEditCoach.value = true;
  editCoachId.value = item.id;
  coachForm.name = item.name;
  coachForm.phone = item.phone;
  coachForm.specialties = item.specialties.join(",");
  coachForm.status = item.status;
  coachForm.hire_date = item.hire_date;
  showCoachModal.value = true;
}

async function saveCoach() {
  // 先存下模式：提示文案不能依赖请求前后的 isEditCoach 状态
  const editing = isEditCoach.value
  try {
    const submitData = {...coachForm}
    if (editing) {
      await updateCoach(editCoachId.value, submitData);
      toast.show("修改保存成功");
    } else {
      const res = await addCoach(submitData);
      // 新增会连带开一个登录账号，后端把「账号 + 初始密码」写在 msg 里，
      // 用后端的提示，管理员才能当面把凭据告诉新教练。
      toast.show(res.msg || "教练新增成功");
    }
    closeCoachModal();
    await loadData();
  } catch (err) {
    toast.show(err.friendlyMessage || "操作失败", "error");
  }
}

async function handleDeleteCoach(item) {
  // 删除是级联的：教练名下的课程、排班、训练计划都会被一起删掉，
  // 学员只解除归属。用应用内确认框把后果和规模都摆出来，别让用户在
  // 浏览器原生 confirm 那个小框里凭记忆点「确定」。
  const ok = await confirmDialog({
    title: "删除教练",
    tone: "danger",
    message:
      "该教练名下的课程、排班、训练计划会一并删除，名下学员将变为「未分配」。\n此操作不可恢复。",
    details: [
      { label: "教练", value: item.name },
      { label: "联系方式", value: item.phone || "—" }
    ],
    confirmText: "删除"
  });
  if (!ok) return;
  try {
    const res = await deleteCoach(item.id);
    toast.show(res.msg || "删除成功");
    await loadData();
  } catch (err) {
    toast.show(err.friendlyMessage || err.msg || "删除失败", "error");
  }
}

async function openCoachDetail(item) {
  statCoachInfo.value = item;
  showStatModal.value = true;
  try {
    const res = await getCoachStat(item.id);
    Object.assign(statData, res.data);
  } catch (e) {
    toast.show("获取统计详情失败");
  }
}

onMounted(async () => {
  await loadData();
  // 统计卡片与列表分开取：卡片是全馆口径，不受分页与搜索影响
  await Promise.all([loadCoachesStat(), loadTodayScheduleCount()]);
});
</script>

<style scoped>
.tag {
  display: inline-block;
  background: #f0f4f9;
  padding: 2px 6px;
  border-radius: 4px;
  margin: 2px;
  font-size: 12px;
}
</style>