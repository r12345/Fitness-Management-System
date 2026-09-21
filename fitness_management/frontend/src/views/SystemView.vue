<template>
  <div>
    <transition name="fade">
      <div v-if="toast.message" class="toast-banner" :class="toast.type">{{ toast.message }}</div>
    </transition>

    <div class="page-header">
      <div>
        <h1>系统配置</h1>
        <p class="page-desc">维护健身房基础信息、系统日志和字典配置。</p>
      </div>
    </div>

    <div class="split-layout">
      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">健身房基础信息</h2>
        </div>
        <div class="panel-body">
          <div class="form-grid">
            <div class="field">
              <label>名称</label>
              <input v-model="form.gym_name" type="text" />
            </div>
            <div class="field">
              <label>联系电话</label>
              <input v-model="form.phone" type="text" />
            </div>
            <div class="field full">
              <label>地址</label>
              <input v-model="form.address" type="text" />
            </div>
            <div class="field full">
              <label>营业时间</label>
              <!-- 原来是纯文本框，格式全靠人记。改成两个时间选择器，
                   提交时拼回 "08:00-23:00" 存进原来的 business_hours 字段，
                   表结构和接口都不用动。 -->
              <div class="time-range">
                <input v-model="businessOpen" type="time" step="60" />
                <span class="time-range-sep">至</span>
                <input v-model="businessClose" type="time" step="60" />
              </div>
              <p v-if="businessHoursUnparsed" class="field-hint">
                原值「{{ rawBusinessHours }}」不是「开始-结束」格式，保存后会按上面选择的时间覆盖。
              </p>
            </div>
          </div>
          <div class="page-actions" style="margin-top: 16px;">
            <button class="btn btn-primary" type="button" @click="save">保存配置</button>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2 class="panel-title">字典配置</h2>
          <div style="margin-left:auto;">
            <button class="btn btn-primary" @click="openDictModal">新增字典</button>
          </div>
        </div>
        <div class="panel-body no-padding">
          <div class="data-table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>字典类型</th>
                  <th>配置项</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in dictionaries" :key="item.dict_type">
                  <td>{{ item.dict_type }}</td>
                  <td>{{ item.value }}</td>
                  <td><span class="badge success">启用</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 系统日志模块：四个身份（超级管理员 / 前台运营 / 健身教练 / 普通会员）的操作都在这里 -->
    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">系统日志</h2>
        <div style="margin-left:auto;">
          <button class="btn btn-secondary btn-sm" type="button" @click="refreshLogs">刷新</button>
        </div>
      </div>
      <div class="panel-body">
        <!-- 四个身份各有多少条操作，开门见山先摆出来 -->
        <div class="role-summary">
          <span
            v-for="item in logMeta.roles"
            :key="item.value"
            class="badge"
            :class="roleBadgeClass(item.value)"
          >
            {{ item.label }} {{ item.count }}
          </span>
          <!-- 两个数要分清楚：身份徽标是全量累计，这里的「当前筛选出」才是下面表格的条数。
               只写一个数的时候看不出哪个是筛选结果。 -->
          <span class="field-hint">
            四个身份累计 {{ logMeta.total }} 条，当前筛选出 {{ logTotal }} 条
          </span>
        </div>

        <div class="filter-bar" style="margin-top:14px;">
          <div class="field">
            <label>身份</label>
            <select v-model="logRoleFilter" @change="()=>{logPage=1;loadLogs()}">
              <option value="">全部身份</option>
              <option v-for="item in logMeta.roles" :key="item.value" :value="item.value">
                {{ item.label }}（{{ item.count }}）
              </option>
            </select>
          </div>
          <div class="field">
            <label>操作类型</label>
            <!-- 选项来自接口（/system/logs/meta），不是前端写死的一份清单：
                 写死过一版（login/config_edit/add/delete），和库里实际存的
                 update_config/add_member 对不上，选中后永远查不到东西。 -->
            <select v-model="logTypeFilter" @change="()=>{logPage=1;loadLogs()}">
              <option value="">全部类型</option>
              <option v-for="item in logMeta.types" :key="item.value" :value="item.value">
                {{ item.label }}（{{ item.count }}）
              </option>
            </select>
          </div>
          <div class="field">
            <label>操作人</label>
            <input v-model="logUserFilter" type="search" placeholder="账号或姓名" @input="debounceLogSearch">
          </div>
          <div class="field">
            <label>起始日期</label>
            <input v-model="logStartDate" type="date" @change="()=>{logPage=1;loadLogs()}">
          </div>
          <div class="field">
            <label>结束日期</label>
            <input v-model="logEndDate" type="date" @change="()=>{logPage=1;loadLogs()}">
          </div>
          <div class="field" style="display:flex;align-items:flex-end;gap:8px;">
            <button class="btn btn-primary" type="button" @click="()=>{logPage=1;loadLogs()}">查询</button>
            <button class="btn btn-secondary" type="button" @click="resetLogFilter()">重置</button>
          </div>
        </div>

        <div class="data-table-wrap no-padding" style="margin-top:14px;">
          <table class="data-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>身份</th>
                <th>操作人</th>
                <th>类型</th>
                <th>操作内容</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!logs_list.length">
                <td colspan="5" style="text-align:center;color:#999;">
                  {{ logLoading ? "加载中…" : "没有符合条件的操作日志" }}
                </td>
              </tr>
              <tr v-for="item in logs_list" :key="item.id">
                <td>{{ formatTime(item.created_at) }}</td>
                <td>
                  <span v-if="item.role_label" class="badge" :class="roleBadgeClass(item.role)">
                    {{ item.role_label }}
                  </span>
                  <!-- 早期回填不上的历史行没有身份，显式标出来而不是留空 -->
                  <span v-else class="badge muted">未记录</span>
                </td>
                <td>
                  <div>{{ item.name || "—" }}</div>
                  <div class="log-account">{{ item.user }}</div>
                </td>
                <td>{{ item.log_type_label || item.log_type }}</td>
                <td>{{ item.content }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <el-pagination
            v-model:current-page="logPage"
            v-model:page-size="logPageSize"
            size="large"
            background
            layout="prev, pager, next"
            :total="logTotal"
            class="mt-4"
            @current-change="(newPage) => { logPage = newPage; loadLogs() }"
        />
      </div>
    </div>

    <!-- 新增字典弹窗 -->
    <el-dialog v-model="dictModalVisible" title="新增字典项" width="500px">
      <div class="form-grid">
        <div class="field">
          <label>字典类型</label>
          <select v-model="dictForm.dict_type">
            <option value="body_part">运动部位</option>
            <option value="equipment_type">器材分类</option>
            <option value="course_type">课程分类</option>
            <option value="member_status">卡状态</option>
            <option value="card_type">办卡类型</option>
            <option value="gender">性别</option>
          </select>
        </div>
        <div class="field">
          <label>字典值</label>
          <input v-model="dictForm.dict_value" type="text" placeholder="请输入配置项名称"/>
        </div>
        <div class="field">
          <label>状态</label>
          <div style="display:flex;gap:16px;">
            <label><input type="radio" v-model="dictForm.status" value="enable"/>启用</label>
            <label><input type="radio" v-model="dictForm.status" value="disable"/>禁用</label>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dictModalVisible = false">取消</el-button>
          <el-button type="primary" @click="submitDict">确认新增</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import {reactive, ref, onMounted} from "vue";
import {useToast} from "../composables/useToast";
import {
  getSystemConfig,
  list_dicts,
  list_system_logs,
  get_log_meta,
  updateSystemConfig,
  create_dicts
} from "../api/system";
import {ElPagination, ElDialog, ElButton} from 'element-plus'

const logTotal = ref(0)
const toast = useToast();
const form = reactive({
  gym_name: null,
  phone: null,
  address: null,
  business_hours: null,
});

// 营业时间在界面上拆成两个时间选择器，提交时再拼回 business_hours
const businessOpen = ref("");
const businessClose = ref("");
const rawBusinessHours = ref("");
// 原值不是「开始-结束」格式时给一句提示，避免用户以为页面把数据弄丢了
const businessHoursUnparsed = ref(false);

/** 从「08:00-23:00」「周一至周日 08:00-23:00」这类文本里抽出首尾两个时间；抽不到返回 null */
function parseBusinessHours(text) {
  if (!text) return null;
  const times = String(text).match(/\d{1,2}:\d{2}/g);
  if (!times || times.length < 2) return null;
  const pad = (t) => {
    const [h, m] = t.split(":");
    return `${h.padStart(2, "0")}:${m}`;
  };
  return { open: pad(times[0]), close: pad(times[1]) };
}

const dictionaries = ref([]);
const logs_list = ref([]);
const total = ref(0);

// -------- 字典弹窗相关 --------
const dictModalVisible = ref(false)
const dictForm = reactive({
  dict_type: "body_part",
  dict_value: "",
  status: "enable"
})

// 打开弹窗，重置表单
function openDictModal() {
  dictForm.dict_type = "body_part"
  dictForm.dict_value = ""
  dictForm.status = "enable"
  dictModalVisible.value = true
}

// 提交新增字典
async function submitDict() {
  if (!dictForm.dict_value) {
    toast.show("请输入字典值");
    return
  }
  try {
    await create_dicts(dictForm)
    dictModalVisible.value = false
    toast.show("新增字典成功")
    await loadDicts() // 新增成功刷新字典列表
  } catch (err) {
    console.error(err)
    toast.show("新增字典失败")
  }
}

// ------------------------------

// 加载系统配置
async function loadSystemConfig() {
  const res = await getSystemConfig();
  form.gym_name = res.data.gym_name;
  form.address = res.data.address;
  form.business_hours = res.data.business_hours;
  form.phone = res.data.phone;

  // 把「周一至周日 08:00-23:00」拆进两个时间选择器
  rawBusinessHours.value = res.data.business_hours || "";
  const parsed = parseBusinessHours(res.data.business_hours);
  businessOpen.value = parsed ? parsed.open : "";
  businessClose.value = parsed ? parsed.close : "";
  businessHoursUnparsed.value = Boolean(res.data.business_hours) && !parsed;
}

// 日志过滤条件
const logTypeFilter = ref(null)
const logRoleFilter = ref(null)
const logUserFilter = ref(null)
const logStartDate = ref(null)
const logEndDate = ref(null)
const logLoading = ref(false)

// 四个身份 + 库里实际出现过的操作类型，都从接口取，前端不写死清单
const logMeta = reactive({ roles: [], types: [], total: 0 })

// 四个身份用不同颜色区分，和「身份」列、顶部概览保持一致
const ROLE_BADGE = {
  admin: "danger",
  reception: "info",
  coach: "success",
  member: "muted"
}
const roleBadgeClass = (role) => ROLE_BADGE[role] || "muted"

// 分页
const logPage = ref(1)
const logPageSize = ref(10)

// 防抖定时器
let logSearchTimer = null
const LOG_DELAY = 350

// 防抖搜索
function debounceLogSearch() {
  if (logSearchTimer) clearTimeout(logSearchTimer)
  logSearchTimer = setTimeout(() => {
    logPage.value = 1
    loadLogs()
  }, LOG_DELAY)
}

// 加载筛选下拉的数据源
async function loadLogMeta() {
  try {
    const res = await get_log_meta()
    logMeta.roles = res.data.roles || []
    logMeta.types = res.data.types || []
    logMeta.total = res.data.total || 0
  } catch (err) {
    console.error(err)
  }
}

// 刷新按钮：条数统计和列表一起更新
async function refreshLogs() {
  await loadLogMeta()
  await loadLogs()
}

// 加载日志列表
async function loadLogs() {
  logLoading.value = true
  try {
    const params = {
      log_type: logTypeFilter.value,
      role: logRoleFilter.value,
      user: logUserFilter.value,
      start_date: logStartDate.value,
      end_date: logEndDate.value,
      page: logPage.value,
      page_size: logPageSize.value,
    }
    const res = await list_system_logs(params)
    logs_list.value = res.data.content_list
    logTotal.value = res.data.total
  } catch (err) {
    toast.show("加载日志失败", "error")
  } finally {
    logLoading.value = false
  }
}

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

// 重置过滤条件
function resetLogFilter() {
  logTypeFilter.value = null
  logRoleFilter.value = null
  logUserFilter.value = null
  logStartDate.value = null
  logEndDate.value = null
  logPage.value = 1
  loadLogs()
}

async function loadDicts() {
  const res = await list_dicts();
  const groupMap = {}
  ;(res.data || []).forEach(item => {
    if (item.status !== 'enable') return
    if (!groupMap[item.dict_type]) {
      groupMap[item.dict_type] = []
    }
    groupMap[item.dict_type].push(item.dict_value)
  })
  dictionaries.value = []
  dictionaries.value.push({dict_type: "运动部位", value: groupMap['body_part']?.join('、') || ''})
  dictionaries.value.push({dict_type: "器材分类", value: groupMap['equipment_type']?.join('、') || ''})
  dictionaries.value.push({dict_type: "课程分类", value: groupMap['course_type']?.join('、') || ''})
  dictionaries.value.push({dict_type: "卡状态", value: groupMap['member_status']?.join('、') || ''})
}

async function save() {
  // 营业时间由两个选择器决定，提交前拼回后端要的 "HH:MM-HH:MM"
  if (!businessOpen.value || !businessClose.value) {
    toast.show("请选择营业的开始时间和结束时间");
    return;
  }
  if (businessOpen.value >= businessClose.value) {
    toast.show("结束时间必须晚于开始时间");
    return;
  }
  form.business_hours = `${businessOpen.value}-${businessClose.value}`;
  try {
    const res = await updateSystemConfig(form)
    if (res && res.code !== 0) {
      toast.show(res.msg || "保存失败");
      return;
    }
    await loadSystemConfig();
    toast.show("系统配置已保存");
  } catch (err) {
    toast.show(err.friendlyMessage || "保存失败");
  }
}

onMounted(async () => {
  await loadSystemConfig();
  // 先取筛选数据源，再查日志：这样首屏的下拉框和列表是同一批数据
  await loadLogMeta();
  await loadLogs();
  await loadDicts()
});
</script>

<style scoped>
/* 四个身份的条数概览：一眼看出各身份各做了多少事 */
.role-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* 日志筛选比其他页多一个「身份」条件，沿用全局的 220px 会折成两行。
   这一页把条件收窄一点、按钮按内容宽度走，一行放得下。 */
.filter-bar {
  gap: 8px;
}

.filter-bar .field {
  width: 150px;
}

/* 最后一个是「查询 / 重置」按钮组，别被 150px 卡住 */
.filter-bar .field:last-child {
  width: auto;
}

/* 操作人单元格的第二行（登录账号），弱化显示但不省略 */
.log-account {
  margin-top: 2px;
  font-size: 12px;
  color: #6b7280;
}
</style>