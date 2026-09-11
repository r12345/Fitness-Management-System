<template>
  <div>
    <transition name="fade">
      <div v-if="toast.message" class="toast-banner" :class="toast.type">{{ toast.message }}</div>
    </transition>

    <div class="page-header">
      <div>
        <h1>{{ isReception ? "器材报修" : "器材管理" }}</h1>
        <p class="page-desc">{{ isReception ? "登记器材报修，跟进维修状态和保养记录。" : "维护器材档案、报修维修、盘点和保养记录。" }}</p>
      </div>
      <div class="page-actions">
        <button v-if="canManage" class="btn btn-primary" type="button" @click="openAdd">新增器材</button>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard label="器材总数" :value="equipmentTotal" unit="台" icon="器" />
      <StatCard label="正常" :value="status_type.normal" unit="台" icon="正" />
      <StatCard label="维修中" :value="status_type.repair" unit="台" icon="修" tone="warn" />
      <StatCard label="已报废" :value="status_type.destroy" unit="台" icon="废" tone="danger" />
    </div>

    <!-- ==========新增搜索筛选表单========== -->
    <div class="panel">
      <div class="panel-body">
        <div class="form-grid" style="grid-template-columns: 1fr 180px 180px auto;gap:12px;align-items:center;">
          <div class="field">
            <label>关键字搜索</label>
            <input v-model="searchForm.keyword" placeholder="输入器材名称/型号搜索" type="text" />
          </div>
          <div class="field">
            <label>器材分类</label>
            <select v-model="searchForm.category">
              <option value="">全部分类</option>
              <option value="有氧器材">有氧器材</option>
              <option value="力量器材">力量器材</option>
              <option value="辅助器材">辅助器材</option>
              <option value="自由重量">自由重量</option>
            </select>
          </div>
          <div class="field">
            <label>器材状态</label>
            <select v-model="searchForm.status">
              <option value="">全部状态</option>
              <option value="正常">正常</option>
              <option value="维修">维修</option>
              <option value="报废">报废</option>
            </select>
          </div>
          <div class="field" style="margin-top:20px;">
            <button class="btn btn-secondary" @click="resetSearch">重置</button>
          </div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">器材列表</h2>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>器材名称</th>
                <th>型号</th>
                <th>分类</th>
                <th>存放位置</th>
                <th>采购时间</th>
                <th>价格</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in list" :key="item.id">
                <td>{{ item.name }}</td>
                <td>{{ item.model }}</td>
                <td>{{ item.category }}</td>
                <td>{{ item.location }}</td>
                <td>{{ item.purchase_date }}</td>
                <td>¥ {{ item.price }}</td>
                <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
                <td>
                  <div class="page-actions">
                    <button class="btn btn-secondary btn-sm" type="button" @click="openRepair(item)">报修</button>
                    <!-- 修改保养按钮：打开保养弹窗 -->
                    <button class="btn btn-secondary btn-sm" type="button" @click="openMaintenance(item)">保养</button>
                    <button v-if="canManage" class="btn btn-secondary btn-sm" type="button" @click="openEdit(item)">编辑</button>
                    <button v-if="canManage" class="btn btn-danger btn-sm" type="button" @click="remove(item)">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ✅复用弹窗：新增 / 编辑 -->
    <div v-if="showAdd" class="modal-mask" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">{{ editId ? "编辑器材" : "新增器材" }}</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="closeModal">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field"><label>器材名称</label><input v-model="form.name" type="text"></div>
            <div class="field"><label>型号</label><input v-model="form.model" type="text"></div>
            <div class="field"><label>分类</label>
              <select v-model="form.category">
                <option value="有氧器械">有氧器械</option>
                <option value="力量器械">力量器械</option>
                <option value="辅助器械">辅助器械</option>
                <option value="自由重量">自由重量</option>
              </select>
            </div>
            <div class="field"><label>存放位置</label>
              <select v-model="form.location">
                <option value="有氧 A区">有氧 A区</option>
                <option value="有氧 B区">有氧 B区</option>
                <option value="有氧 C区">有氧 C区</option>
                <option value="有氧 D区">有氧 D区</option>
                <option value="力量 A区">力量 A区</option>
                <option value="力量 B区">力量 B区</option>
                <option value="力量 C区">力量 C区</option>
                <option value="力量 D区">力量 D区</option>
              </select>
            </div>
            <div class="field"><label>采购时间</label><input v-model="form.purchase_date" type="date"></div>
            <div class="field"><label>价格</label><input v-model.number="form.price" type="number"></div>
            <div class="field"><label>状态</label><input v-model="form.status" type="text"></div>
            <div class="field"><label>备注</label><input v-model="form.remark" type="text"></div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="closeModal">取消</button>
          <button class="btn btn-primary" type="button" @click="saveEquipment">{{ editId ? "保存修改" : "保存" }}</button>
        </div>
      </div>
    </div>

    <!-- 报修弹窗 -->
    <div v-if="repairTarget" class="modal-mask" @click.self="repairTarget = null">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">报修登记：{{ repairTarget.name }}</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="repairTarget = null">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field full"><label>故障描述</label><textarea v-model="repair_data.description"></textarea></div>
            <div class="field"><label>维修费用</label><input v-model.number="repair_data.cost" type="number"></div>
            <div class="field"><label>维修时间</label><input v-model="repair_data.repair_time" type="date"></div>
            <div class="field"><label>备注</label><input v-model="repair_data.remark" type="text"></div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="repairTarget = null">取消</button>
          <button class="btn btn-primary" type="button" @click="submitRepair">提交维修</button>
        </div>
      </div>
    </div>

    <!-- ✅保养登记弹窗【新增】 -->
    <div v-if="maintainTarget" class="modal-mask" @click.self="closeMaintainModal">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">保养登记：{{ maintainTarget.name }}</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="closeMaintainModal">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field">
              <label>保养人</label>
              <input v-model="maintainForm.person" type="text" placeholder="填写保养人员姓名"/>
            </div>
            <div class="field">
              <label>保养时间</label>
              <input v-model="maintainForm.maintenance_time" type="datetime-local"/>
            </div>
            <div class="field full">
              <label>保养内容</label>
              <textarea v-model="maintainForm.content" placeholder="填写保养项目、检查情况"></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="closeMaintainModal">取消</button>
          <button class="btn btn-primary" type="button" @click="submitMaintenance">提交保养记录</button>
        </div>
      </div>
    </div>

    <el-pagination
      v-model:current-page="searchForm.page"
      v-model:page-size="searchForm.page_size"
      size="large"
      background
      layout="prev, pager, next"
      :total="total"
      class="mt-4"
      @current-change="fetchEquipmentList"
    />
  </div>
</template>

<script setup>
import {computed, onMounted, reactive, ref, watch} from "vue";
import { useToast } from "../composables/useToast";
import StatCard from "../components/StatCard.vue";
import {
  create_equipment,
  create_maintenance, create_repair,
  delete_equipment,
  getEquipmentList,
  update_equipment
} from "../api/equipment.js";
import {ElPagination} from "element-plus";
import {useUserStore} from "../stores/user.js";
import {getEquipmentStatistics} from "../api/statistics.js";
const userStore = useUserStore();
const toast = useToast();
const role = userStore.role;
const canManage = role === "admin";
const isReception = role === "reception";

const list = ref([]);
const showAdd = ref(false);
const editId = ref(null);
const repairTarget = ref(null);

// ==========保养弹窗状态【新增】==========
const maintainTarget = ref(null);
const maintainForm = reactive({
  person: "",
  maintenance_time: "",
  content: ""
});

// 分页
const total = ref(0);

const form = reactive({
  name: '',
  model: "",
  category: "有氧器械",
  location: "有氧 A区",
  purchase_date:'',
  price: 0,
  status: "正常",
  remark: ""
});

// 搜索表单
const searchForm = reactive({
  keyword: "",
  category: "",
  status: "",
  page: 1,
  page_size: 10
})
let searchTimer = null;

watch(() => searchForm.keyword, () => {
  if(searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(()=>{
    fetchEquipmentList()
  }, 300)
})

watch([()=>searchForm.category, ()=>searchForm.status], ()=>{
  fetchEquipmentList()
})

async function fetchEquipmentList(){
  const params = {
    keyword: searchForm.keyword || undefined,
    category: searchForm.category || undefined,
    status: searchForm.status || undefined,
    page: searchForm.page,
    page_size: searchForm.page_size
  }
  console.log("请求参数", params)
  const res = await getEquipmentList(params);
  console.log("请求结果", res)
  total.value = res.data.total
  list.value = res.data.items
}

function resetSearch(){
  searchForm.keyword = ""
  searchForm.category = ""
  searchForm.status = ""
  searchForm.page = 1
  fetchEquipmentList()
}

function statusClass(status) {
  if (status === "正常") return "success";
  if (status === "维修") return "warn";
  return "muted";
}

function openAdd(){
  editId.value = null
  form.name = ''
  form.model = ''
  form.category = "有氧器械"
  form.location = "有氧 A区"
  form.purchase_date = ''
  form.price = 0
  form.status = "正常"
  form.remark = ''
  showAdd.value = true
}

function openEdit(item){
  editId.value = item.id
  form.name = item.name
  form.model = item.model
  form.category = item.category
  form.location = item.location
  form.purchase_date = item.purchase_date
  form.price = item.price
  form.status = item.status
  form.remark = item.remark ?? ""
  showAdd.value = true
}

function closeModal(){
  showAdd.value = false
  editId.value = null
}

async function saveEquipment() {
  try{
    let res
    if(editId.value){
      res = await update_equipment(editId.value, form)
    }else{
      res = await create_equipment(form)
    }
    if (res.code === 0) {
      await fetchEquipmentList()
      closeModal()
      toast.show(editId.value ? "器材已修改" : "器材已新增");
    }
  }catch(err){
    toast.show(editId.value ? "修改失败" : "新增失败");
  }
}

async function remove(item) {
  try {
    const res = await delete_equipment(item.id)
    console.log(res)
    if (res.code === 0) {
      await fetchEquipmentList()
      toast.show("器材已删除");
    } else {
      toast.show(res.msg || "删除失败")
    }
  } catch (err) {
    console.error(err)
    toast.show("请求异常，删除失败")
  }
}

const repair_data = reactive({
  description:'',
  cost:0,
  repair_time:'',
  remark:''
})

async function openRepair(item) {
  repairTarget.value = item;
}

async function submitRepair() {
  console.log(repair_data)
  const res = await create_repair(repairTarget.value.id,repair_data);
  console.log(res)
  repairTarget.value.status = "维修";
  repairTarget.value = null;
  repair_data.repair_time = '';
  repair_data.description = '';
  repair_data.cost = 0;
  repair_data.remark = '';
  toast.show("报修已登记");
}

// =====================保养相关方法【新增】=====================
/**打开保养弹窗 */
function openMaintenance(item){
  maintainTarget.value = item
  //清空表单
  maintainForm.person = ""
  maintainForm.maintenance_time = ""
  maintainForm.content = ""
}

/**关闭保养弹窗 */
function closeMaintainModal(){
  maintainTarget.value = null
  maintainForm.person = ""
  maintainForm.maintenance_time = ""
  maintainForm.content = ""
}
const equipmentTotal = ref(0);
const status_type=ref({
  normal: 0,
  repair: 0,
  destroy: 0
})

async function getStatistics(){
  const res = await getEquipmentStatistics()
  console.log(res)
  equipmentTotal.value = res.data.total
  // 重置归零
  status_type.value.normal = 0
  status_type.value.repair = 0
  status_type.value.destroy = 0

  //遍历后端数组
  res.data.status_type.forEach(item => {
    if(item.status === '正常'){
      status_type.value.normal = item.count
    }else if(item.status === '维修'){
      status_type.value.repair = item.count
    }else if(item.status === '报废'){
      status_type.value.destroy = item.count
    }
    // status为空字符串直接跳过
  })
}
/**提交保养记录，调用 create_maintenance接口 */
async function submitMaintenance(){
  if(!maintainForm.person || !maintainForm.maintenance_time || !maintainForm.content){
    toast.show("请完整填写保养人、保养时间、保养内容")
    return
  }
  try{
    const res = await create_maintenance(maintainTarget.value.id, maintainForm)
    console.log(res)
    if(res.code === 0){
      toast.show("保养记录保存成功")
      closeMaintainModal()
    }else{
      toast.show(res.msg || "保养记录保存失败")
    }
  }catch (e){
    console.error(e)
    toast.show("请求异常，提交保养失败")
  }
}

onMounted(async () => {
  await fetchEquipmentList()
  await getStatistics()
})
</script>
