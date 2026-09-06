<template>
  <div>
    <transition name="fade">
      <div v-if="toast.message.value" class="toast-banner">{{ toast.message.value }}</div>
    </transition>
    <div class="page-header">
      <div>
        <h1>{{ isReception ? "会员开卡续费" : "会员管理" }}</h1>
        <p class="page-desc">{{ isReception ? "办理会员开卡、续费，查询消费流水和会员详情。" : "维护会员档案、办卡续费、消费记录和会员明细。" }}</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary" type="button" @click="changeAdd">新增会员</button>
      </div>
    </div>

    <div class="panel">
      <div class="panel-body">
        <div class="filter-bar">
          <div class="field">
            <label>关键词</label>
            <input v-model="keyword" type="search" placeholder="会员姓名或手机号" @input="debounceSearch">
          </div>
          <div class="field">
            <label>卡状态</label>
            <select v-model="statusFilter" @change="()=>{currentPage=1;loadList()}">
              <option value="">全部状态</option>
              <option value="正常">正常</option>
              <option value="过期">过期</option>
              <option value="暂停">暂停</option>
            </select>
          </div>
          <div class="field">
            <label>办卡类型</label>
            <select v-model="cardTypeFilter" @change="()=>{currentPage=1;loadList()}">
              <option value="">全部卡种</option>
              <option value="月卡">月卡</option>
              <option value="季卡">季卡</option>
              <option value="年卡">年卡</option>
              <option value="次卡">次卡</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">会员列表</h2>
        <span>共 {{ total }} 条</span>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>会员编号</th>
                <th>姓名</th>
                <th>手机号</th>
                <th>性别</th>
                <th>年龄</th>
                <th>办卡类型</th>
                <th>到期时间</th>
                <th>余额</th>
                <th>卡状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id">
                <td>{{ item.id }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.phone }}</td>
                <td>{{ item.gender ?? '男' }}</td>
                <td>{{ item.age ?? 0 }}</td>
                <td>{{ item.card_type }}</td>
                <td>{{ item.card_expire }}</td>
                <td>¥ {{ (item.balance ?? 0).toLocaleString("zh-CN") }}</td>
                <td>{{ item.status }}</td>
                <td>
                  <div class="page-actions">
                    <button class="btn btn-secondary btn-sm" type="button" @click="getDetail(item)">详情</button>
                    <button class="btn btn-secondary btn-sm" type="button" @click="openRenew(item)">续费</button>
                    <button class="btn btn-danger btn-sm" type="button" @click="removeMember(item)">删除</button>
                    <button class="btn btn-danger btn-sm" type="button" @click="changeEdit(item)">编辑</button>
                    <button class="btn btn-danger btn-sm" type="button" @click="changeState(item)">编辑状态</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          size="large"
          background
          layout="prev, pager, next"
          :total="total"
          class="mt-4"
          @current-change="(newPage) => { currentPage = newPage; loadList() }"
        />
      </div>
    </div>

    <!-- 新增会员弹窗 -->
   <!-- 新增 / 修改会员弹窗，同一个弹窗两种模式 -->
<div v-if="showModal" class="modal-mask" @click.self="showModal = false">
  <div class="modal">
    <div class="modal-header">
      <h3 class="panel-title">{{ isEdit ? "修改会员" : "新增会员" }}</h3>
      <button class="btn btn-secondary btn-sm" type="button" @click="showModal = false">关闭</button>
    </div>
    <div class="modal-body">
      <div class="form-grid">
        <div class="field"><label>姓名</label><input v-model="form.name" type="text"></div>
        <div class="field"><label>手机号</label><input v-model="form.phone" type="text"></div>
        <div class="field"><label>性别</label>
          <select v-model="form.gender">
            <option>男</option>
            <option>女</option>
          </select>
        </div>
        <div class="field"><label>年龄</label><input v-model.number="form.age" type="number"></div>
        <div class="field"><label>办卡类型</label>
          <select v-model="form.card_type">
            <option>月卡</option>
            <option>季卡</option>
            <option>年卡</option>
            <option>次卡</option>
          </select>
        </div>
        <div class="field"><label>开卡时间</label><input v-model="form.card_start" type="date"></div>
        <div class="field"><label>到期时间</label><input v-model="form.card_expire" type="date"></div>
        <div class="field"><label>余额</label><input v-model.number="form.balance" type="number"></div>
        <div class="field"><label>状态</label>
          <select v-model="form.status">
            <option>正常</option>
            <option>过期</option>
            <option>暂停</option>
          </select>
        </div>
        <div class="field"><label>备注</label><input v-model="form.remark" type="text"></div>
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" type="button" @click="showModal = false">取消</button>
      <button class="btn btn-primary" type="button" @click="saveMember">{{ isEdit ? "修改保存" : "保存" }}</button>
    </div>
  </div>
</div>


    <!-- ==========会员详情弹窗========== -->
    <div v-if="showDetailModal" class="modal-mask" @click.self="showDetailModal=false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3 class="panel-title">会员详情 - {{ detailInfo?.name }}</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showDetailModal=false">关闭</button>
        </div>
        <div class="modal-body">
          <!-- 基础信息区域 -->
          <div class="panel mb-3">
            <div class="panel-header"><h4>基础信息</h4></div>
            <div class="panel-body">
              <div class="form-grid">
                <div class="field"><label>会员编号</label>{{ detailInfo?.id }}</div>
                <div class="field"><label>姓名</label>{{ detailInfo?.name }}</div>
                <div class="field"><label>手机号</label>{{ detailInfo?.phone }}</div>
                <div class="field"><label>性别</label>{{ detailInfo?.gender }}</div>
                <div class="field"><label>年龄</label>{{ detailInfo?.age }}</div>
                <div class="field"><label>办卡类型</label>{{ detailInfo?.card_type }}</div>
                <div class="field"><label>开卡时间</label>{{ detailInfo?.card_start }}</div>
                <div class="field"><label>到期时间</label>{{ detailInfo?.card_expire }}</div>
                <div class="field"><label>余额</label>¥ {{ detailInfo?.balance }}</div>
                <div class="field"><label>卡状态</label>{{ detailInfo?.status }}</div>
              </div>
            </div>
          </div>

          <!-- 消费流水 -->
          <div class="panel mb-3">
            <div class="panel-header"><h4>消费记录</h4></div>
            <div class="panel-body no-padding">
              <table class="data-table">
                <thead>
                <tr>
                  <th>ID</th>
                  <th>项目</th>
                  <th>金额</th>
                  <th>操作人</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="c in detailConsumptions" :key="c.id">
                  <td>{{ c.id }}</td>
                  <td>{{ c.item }}</td>
                  <td>¥{{ c.amount }}</td>
                  <td>{{ c.operator }}</td>
                </tr>
                <tr v-if="detailConsumptions.length===0">
                  <td colspan="4">暂无消费记录</td>
                </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 签到记录 -->
          <div class="panel mb-3">
            <div class="panel-header"><h4>签到记录</h4></div>
            <div class="panel-body no-padding">
              <table class="data-table">
                <thead>
                <tr>
                  <th>ID</th>
                  <th>签到日期</th>
                  <th>离开时间</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="ck in detailCheckins" :key="ck.id">
                  <td>{{ ck.id }}</td>
                  <td>{{ ck.checkin_date }}</td>
                  <td>{{ ck.leave_time }}</td>
                </tr>
                <tr v-if="detailCheckins.length===0">
                  <td colspan="3">暂无签到记录</td>
                </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 预约记录 -->
          <div class="panel">
            <div class="panel-header"><h4>预约记录</h4></div>
            <div class="panel-body no-padding">
              <table class="data-table">
                <thead>
                <tr>
                  <th>ID</th>
                  <th>预约时间</th>
                  <th>状态</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="ap in detailAppointments" :key="ap.id">
                  <td>{{ ap.id }}</td>
                  <td>{{ ap.appointment_time }}</td>
                  <td>{{ ap.status }}</td>
                </tr>
                <tr v-if="detailAppointments.length===0">
                  <td colspan="3">暂无预约记录</td>
                </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDetailModal=false">关闭</button>
        </div>
      </div>
    </div>
<!-- ==========续费弹窗========== -->
<div v-if="showRenewModal" class="modal-mask" @click.self="showRenewModal = false">
  <div class="modal">
    <div class="modal-header">
      <h3 class="panel-title">会员续费 - {{ renewMemberInfo?.name }}</h3>
      <button class="btn btn-secondary btn-sm" type="button" @click="showRenewModal = false">关闭</button>
    </div>
    <div class="modal-body">
      <div class="form-grid">
        <div class="field">
          <label>续费月数</label>
          <input v-model.number="renewForm.months" type="number" min="1" placeholder="输入续费月数">
        </div>
        <div class="field">
          <label>续费金额(元)</label>
          <input v-model.number="renewForm.amount" type="number" min="0" placeholder="实际缴费金额">
        </div>
        <div class="field">
          <label>办卡类型</label>
          <select v-model="renewForm.card_type" >
            <option value="次卡">次卡</option>
            <option value="月卡">月卡</option>
            <option value="学期卡">学期卡</option>
            <option value="年卡">年卡</option>
          </select>
        </div>
        <div class="field">
          <label>支付方式</label>
          <select  v-model="renewForm.pay_method">
            <option value="微信">微信</option>
            <option value="支付宝">支付宝</option>
            <option value="现金">现金</option>
            <option value="银行卡">银行卡</option>
          </select>
        </div>
        <div class="field">
          <label>备注</label>
          <input v-model="renewForm.remark" type="text" placeholder="续费备注信息">
        </div>
        <div class="field">
          <label>操作人</label>
          <input v-model="renewForm.operator" type="text" placeholder="操作人姓名">
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" type="button" @click="showRenewModal = false">取消</button>
      <button class="btn btn-primary" type="button" @click="saveRenew">确认续费</button>
    </div>
  </div>
</div>
<!-- ==========编辑会员状态弹窗========== -->
<div v-if="showStateModal" class="modal-mask" @click.self="showStateModal = false">
  <div class="modal">
    <div class="modal-header">
      <h3 class="panel-title">修改会员状态 - {{ stateMemberInfo?.name }}</h3>
      <button class="btn btn-secondary btn-sm" type="button" @click="showStateModal = false">关闭</button>
    </div>
    <div class="modal-body">
      <div class="form-grid">
        <div class="field">
          <label>当前会员</label>
          <span>{{ stateMemberInfo?.name }}｜{{ stateMemberInfo?.phone }}</span>
        </div>
        <div class="field">
          <label>选择卡状态</label>
          <select v-model="stateForm.status">
            <option value="正常">正常</option>
            <option value="过期">过期</option>
            <option value="暂停">暂停</option>
          </select>
        </div>
        <div class="field">
          <label>状态变更备注</label>
          <input v-model="stateForm.remark" type="text" placeholder="填写状态变更原因，选填">
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" type="button" @click="showStateModal = false">取消</button>
      <button class="btn btn-primary" type="button" @click="saveMemberState">保存状态</button>
    </div>
  </div>
</div>
  </div>
</template>

<script setup>
import {computed, reactive, ref} from "vue";
import {useAuth} from "../composables/useAuth";
import {ElPagination} from 'element-plus'
import {useToast} from "../composables/useToast";
import {addMember, deleteMember, get_detail, getMemberList, renewMember, updateMember,updateMemberStatus} from "../api/member.js";
import {onMounted} from "vue";
import {useRouter} from "vue-router";
import {useUserStore} from "../stores/user.js";
const userStore = useUserStore()
const router = useRouter();
const auth = useAuth();
const toast = useToast();

// 过滤条件
const keyword = ref("");
const statusFilter = ref("");
const cardTypeFilter = ref("");

const isEdit = ref(false);
// 修改状态弹窗
const showStateModal = ref(false)
const stateMemberInfo = ref(null)
const stateForm = reactive({
  status: "正常",
  remark: ""
})
// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const items = ref([])

const showModal = ref(false);

// =========详情弹窗变量========
const showDetailModal = ref(false)
const detailInfo = ref(null)
const detailConsumptions = ref([])
const detailCheckins = ref([])
const detailAppointments = ref([])
const nowMemberId = ref(null)
// 定时器标记
let searchTimer = null
const DELAY = 350

// 打开修改状态弹窗
function changeState(item) {
  stateMemberInfo.value = item
  showStateModal.value = true
  // 回显原有状态
  stateForm.status = item.status
  stateForm.remark = ""
}

// 保存会员状态修改
async function saveMemberState() {
  try {
    // 调用你已经导入好的 updateMemberStatus api
    const res = await updateMemberStatus(stateMemberInfo.value.id, stateForm)
    if(res.code === 0){
      toast.show("会员状态修改成功")
      showStateModal.value = false
      await loadList() // 刷新列表
    }else{
      toast.show(res.msg || "状态修改失败")
    }
  } catch (err) {
    console.error(err)
    toast.show("状态修改请求异常")
  }
}

// 防抖函数
function debounceSearch() {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadList()
  }, DELAY)
}

function changeEdit(item){
  isEdit.value= true
  showModal.value = true
  nowMemberId.value = Number(item.id)
  form.name = item.name
  form.gender = item.gender
  form.phone = item.phone
  form.age = item.age
  form.card_type = item.card_type
  form.card_start = item.card_start
  form.card_expire = item.card_expire
  form.balance = item.balance
  form.status = item.status
  form.remark = item.remark
}

function changeAdd(){
  isEdit.value= false
  showModal.value = true
  form.name = ''
  form.gender = ''
  form.phone = ''
  form.age = 0
  form.card_type = 'item.card_type'
  form.card_start = null
  form.card_expire = null
  form.balance = 0
  form.status = '正常'
  form.remark = '无'
}


const form = reactive({
  name: "",
  gender: "",
  phone: "",
  age: 0,
  card_type: "月卡",
  card_start: "",
  card_expire: "",
  balance: 0,
  status: "正常",
  remark: ''
});
form.card_start = new Date().toISOString().split('T')[0]
const showRenewModal = ref(false)
const renewMemberInfo = ref(null)
const renewForm = reactive({
  months: 0,
  amount: 0,
  remark: "",
  card_type:'',
  pay_method: "",
  operator: userStore.role_name
})

// async function updateMemberStatus(){
//
// }

// 打开续费弹窗
function openRenew(item) {
  renewMemberInfo.value = item
  // 重置续费表单
  renewForm.months = 0
  renewForm.amount = 0
  renewForm.pay_method = "微信"
  renewForm.remark = "会员续费"
  renewForm.card_type='月卡'
  showRenewModal.value = true
}


async function saveRenew(){
  const res = await renewMember(renewMemberInfo.value.id, renewForm);
  if ( res.code === 0) {
    await loadList()
     toast.show(renewMemberInfo.value.name+res.msg )
  showRenewModal.value = false
  }else{
    toast.show(renewMemberInfo.value.name+'续费失败' )
  }
}
const isReception = computed(() => auth.currentRole.value === "reception");

async function loadList() {
  try {
    const res = await getMemberList({
      page: currentPage.value,
      size: pageSize.value,
      keyword: keyword.value,
      status: statusFilter.value,
      card_type: cardTypeFilter.value
    });
    console.log(res)
    items.value = res.data.items
    total.value = res.data.total
  } catch (err) {
    toast.show("加载列表失败")
  }
}

onMounted(async () => {
  await loadList()
})

// 点击详情
async function getDetail(item) {
  try {
    const res = await get_detail(item.id)
    console.log(res.data)
    detailInfo.value = res.data.items
    detailConsumptions.value = res.data.consumptions
    detailCheckins.value = res.data.checkins
    detailAppointments.value = res.data.appointments
    showDetailModal.value = true
  } catch (err) {
    toast.show("获取详情失败")
  }
}



async function saveMember() {
  try {
    let res;
    if (isEdit.value) {
      console.log(form)
      res = await updateMember(nowMemberId.value, form);
      // 如果后端返回code判断，开启下面这行
      console.log(res)
    } else {
      console.log(form)
      res = await addMember(form);
      console.log(res)
    }

    // 根据模式动态提示
    toast.show(isEdit.value ? "修改成功" : "新增成功");

    await loadList() // 优先加载数据，再关闭弹窗
    showModal.value = false;

  } catch (e) {
    console.error(e);
    toast.show(isEdit.value ? "修改失败" : "新增失败");
  }
}




async function removeMember(item) {
  try {
    await deleteMember(item.id);
    toast.show("会员已删除");
    await loadList()
  } catch (e) {
    toast.show("删除失败")
  }
}
</script>

<style scoped>
/* 加大详情弹窗宽度 modal-lg */
:deep(.modal-lg) {
  width: 850px;
  max-width: 95vw;
}

.mb-3 {
  margin-bottom: 16px;
}
</style>
