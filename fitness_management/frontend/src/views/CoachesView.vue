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
      <StatCard label="在职教练" v-model:value="stat_total_coach" unit="人" icon="人" />
      <StatCard label="今日排课" v-model:value="stat_today_course" unit="节" icon="排" />
      <StatCard label="本月授课课时" v-model:value="stat_sum_hours" unit="课时" icon="课" tone="warn" />
      <StatCard label="平均评分" v-model:value="stat_avg_score" unit="分" icon="分" />
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
import {getCoachStatistics} from '../api/statistics.js'
import { useToast } from "../composables/useToast";

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

function calcPageStat() {
  const validList = list.value;
  stat_sum_hours.value = validList.reduce((s, i) => s + (i.hours || 0), 0);
  const scoreArr = validList.filter((i) => i.score);
  stat_avg_score.value = scoreArr.length
    ? (scoreArr.reduce((s, i) => s + i.score, 0) / scoreArr.length).toFixed(2)
    : 0;
  stat_total_coach.value = total.value;
}

async function loadData() {
  try {
    const res = await getCoachList(queryForm.value);
    list.value = res.data.items;
    total.value = res.data.total;
    calcPageStat();
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
  try {
    const submitData = {...coachForm}
    if(isEditCoach.value){
      console.log(submitData)
      await updateCoach(editCoachId.value, submitData);
      toast.show("修改保存成功");
    }else{
      console.log(submitData)
      await addCoach(submitData);
      toast.show("教练新增成功");
    }
    closeCoachModal();
    await loadData();
  } catch (err) {
    toast.show("操作失败");
  }
}

async function handleDeleteCoach(item) {
  if (!confirm(`确认删除教练【${item.name}】吗？`)) return;
  try {
    await deleteCoach(item.id);
    toast.show("删除成功");
    await loadData();
  } catch (err) {
    toast.show("删除失败");
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