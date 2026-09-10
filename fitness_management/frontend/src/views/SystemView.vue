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
              <input v-model="form.business_hours" type="text" />
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

    <!-- 系统日志模块：增加查询表单 + 分页 -->
    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">系统日志</h2>
      </div>
      <div class="panel-body">
        <div class="filter-bar">
          <div class="field">
            <label>日志类型</label>
            <select v-model="logTypeFilter" @change="()=>{logPage=1;loadLogs()}">
              <option value="">全部类型</option>
              <option value="login">登录</option>
              <option value="config_edit">修改配置</option>
              <option value="add">新增数据</option>
              <option value="delete">删除数据</option>
            </select>
          </div>
          <div class="field">
            <label>操作人</label>
            <input v-model="logUserFilter" type="search" placeholder="操作人姓名" @input="debounceLogSearch">
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

        <div class="data-table-wrap no-padding">
          <table class="data-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>类型</th>
                <th>操作人</th>
                <th>操作内容</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in logs_list" :key="index">
                <td>{{ formatTime(item.created_at) }}</td>
                <td>{{ item.log_type }}</td>
                <td>{{ item.user }}</td>
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
import {getSystemConfig, list_dicts, list_system_logs, updateSystemConfig, create_dicts} from "../api/system";
import {ElPagination, ElDialog, ElButton} from 'element-plus'

const logTotal = ref(0)
const toast = useToast();
const form = reactive({
  gym_name: null,
  phone: null,
  address: null,
  business_hours: null,
});

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
  console.log(res)
  form.gym_name = res.data.gym_name;
  form.address = res.data.address;
  form.business_hours = res.data.business_hours;
  form.phone = res.data.phone;
}

// 日志过滤条件
const logTypeFilter = ref(null)
const logUserFilter = ref(null)
const logStartDate = ref(null)
const logEndDate = ref(null)

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

// 加载日志列表
async function loadLogs() {
  try {
    const params = {
      log_type: logTypeFilter.value,
      user: logUserFilter.value,
      start_date: logStartDate.value,
      end_date: logEndDate.value,
      page: logPage.value,
      page_size: logPageSize.value,
    }
    console.log(params)
    const res = await list_system_logs(params)
    logs_list.value = res.data.content_list
    logTotal.value = res.data.total
  } catch (err) {
    console.error(err)
    toast.show("加载日志失败")
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
  logUserFilter.value = null
  logStartDate.value = null
  logEndDate.value = null
  logPage.value = 1
  loadLogs()
}

async function loadDicts() {
  const res = await list_dicts();
  console.log(res);
  const groupMap = {}
  res.data.forEach(item => {
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
  const res = await updateSystemConfig(form)
  console.log(res)
  await loadSystemConfig();
  toast.show("系统配置已保存");
}

onMounted(async () => {
  await loadSystemConfig();
  await loadLogs();
  await loadDicts()
});
</script>