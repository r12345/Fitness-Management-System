<template>
  <div>
    <transition name="fade">
      <!-- useToast 返回的是 reactive({message: ref()})，模板里读 toast.message 才会解包。
           写成 toast.message.value 拿到的是 undefined，提示条永远不会显示。 -->
      <div v-if="toast.message" class="toast-banner" :class="toast.type">{{ toast.message }}</div>
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
                <th>剩余</th>
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
                <!-- 卡状态由后端按到期时间推导，这里把「还有几天」直接摆出来，
                     两者对不上时一眼就能看出来 -->
                <td>
                  <span :class="remainClass(item)">{{ cardRemain(item) }}</span>
                </td>
                <td>¥ {{ (item.balance ?? 0).toLocaleString("zh-CN") }}</td>
                <td>{{ item.status }}</td>
                <td>
                  <div class="page-actions">
                    <button class="btn btn-secondary btn-sm" type="button" @click="getDetail(item)">详情</button>
                    <button class="btn btn-secondary btn-sm" type="button" @click="openRenew(item)">续费</button>
                    <button class="btn btn-secondary btn-sm" type="button" @click="changeEdit(item)">编辑</button>
                    <button class="btn btn-secondary btn-sm" type="button" @click="changeState(item)">编辑状态</button>
                    <button class="btn btn-danger btn-sm" type="button" @click="removeMember(item)">删除</button>
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
        <!-- 卡状态不再是表单字段：它由「到期时间」推导，手填只会造出
             「卡已过期一年却标着正常」这种自相矛盾的数据。
             需要人工停卡，用列表里的「编辑状态」。 -->
        <div class="field"><label>卡状态</label>
          <p class="field-hint">{{ autoStatusHint }}</p>
        </div>
        <div class="field"><label>备注</label><input v-model="form.remark" type="text"></div>
        <div class="field">
          <label>归属教练</label>
          <!-- 归属教练必须显式提交：后端只在请求体里带了这一项时才覆盖，
               不然「编辑一下手机号」会把学员从他的教练名下清掉。 -->
          <select v-model.number="form.coach_id">
            <option :value="null">不指定（未分配）</option>
            <option v-for="c in coachOptions" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
      </div>
      <!-- 办完卡的人得能登进会员中心看自己的打卡与预约，所以新增时会顺带开账号。 -->
      <p v-if="!isEdit" class="field-hint">
        保存后会同时为该会员创建登录账号：账号为上面填写的手机号，初始密码 123456，请转告本人。
      </p>
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
import {confirmDialog} from "../composables/useConfirm.js";
import {addMember, deleteMember, get_detail, getMemberList, renewMember, updateMember,updateMemberStatus} from "../api/member.js";
import {getCoachList} from "../api/coach.js";
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
  // 归属教练要回填：留空再保存会把学员从教练名下摘掉
  form.coach_id = item.coach_id ?? null
}

/** 今天（本地时区）。用 toISOString() 拿到的是 UTC，北京时间 0-8 点会算成前一天 */
function todayLocal() {
  const d = new Date()
  const month = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  return `${d.getFullYear()}-${month}-${day}`
}

function changeAdd(){
  isEdit.value= false
  nowMemberId.value = null
  showModal.value = true
  form.name = ''
  form.gender = '男'
  form.phone = ''
  form.age = 0
  // 原来是 form.card_type = 'item.card_type'，把字面量当变量用了，
  // 新增会员的办卡类型一直被写成 "item.card_type"
  form.card_type = '月卡'
  form.card_start = todayLocal()
  // 必须清空，否则「先编辑 A、再新增 B」时 B 会沿用 A 的到期时间
  form.card_expire = null
  form.balance = 0
  form.status = '正常'
  form.remark = '无'
  form.coach_id = null
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
  remark: '',
  // 归属教练：办卡时可直接指派，之后也能在「编辑」里改派（null = 未分配）
  coach_id: null
});

// 归属教练下拉的候选。会员管理页只有管理员/前台能进，接口对他们放行。
const coachOptions = ref([]);

async function loadCoachOptions() {
  try {
    const res = await getCoachList({ page: 1, page_size: 100 });
    coachOptions.value = res.data?.items || [];
  } catch (err) {
    // 取不到教练列表不影响其余功能，只是这一项没法改派
    console.warn("加载教练列表失败：", err?.friendlyMessage || err);
  }
}
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

/**
 * 卡状态由后端按 card_expire（到期时间）推导，前端把这些天数换算出来摆在列表里，
 * 「状态」和「到期时间」对不对得上一眼就能看出来。
 */
function cardRemain(item) {
  const days = daysToExpire(item.card_expire);
  if (days === null) return "—";
  if (days > 0) return `剩 ${days} 天`;
  if (days === 0) return "今天到期";
  return `已过期 ${-days} 天`;
}

function remainClass(item) {
  const days = daysToExpire(item.card_expire);
  if (days === null) return "remain-ok";
  if (days < 0) return "remain-expired";
  if (days <= 7) return "remain-soon";
  return "remain-ok";
}

/** 把 YYYY-MM-DD 换算成距今天数；解析不出来返回 null */
function daysToExpire(value) {
  if (!value) return null;
  // 后端这一列是 DATE，取前 10 位即可（同时兼容带时间的字符串）
  const expire = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(expire.getTime())) return null;
  const today = new Date(`${todayLocal()}T00:00:00`);
  return Math.round((expire - today) / 86400000);
}

/** 表单里实时预告保存后的卡状态，免得用户以为状态还得自己选 */
const autoStatusHint = computed(() => {
  if (form.status === "暂停") return "当前是人工设置的「暂停」，保存后保持不变";
  const days = daysToExpire(form.card_expire);
  if (days === null) return "请先选择到期时间，卡状态会随之自动判定";
  return days < 0
    ? "到期时间已过 → 保存后自动标记为「过期」"
    : "到期时间未到 → 保存后自动标记为「正常」";
});

async function loadList() {
  try {
    const res = await getMemberList({
      page: currentPage.value,
      // 后端这个参数叫 page_size，之前传的是 size：
      // axios 会把 undefined 丢掉，后端于是永远用默认的 10 条，改每页条数不生效
      page_size: pageSize.value,
      keyword: keyword.value,
      status: statusFilter.value,
      card_type: cardTypeFilter.value
    });
    items.value = res.data.items
    total.value = res.data.total
  } catch (err) {
    toast.show("加载列表失败", "error")
  }
}

onMounted(async () => {
  await loadList()
  await loadCoachOptions()
})

// 点击详情
async function getDetail(item) {
  try {
    const res = await get_detail(item.id)
    detailInfo.value = res.data.items
    detailConsumptions.value = res.data.consumptions
    detailCheckins.value = res.data.checkins
    detailAppointments.value = res.data.appointments
    showDetailModal.value = true
  } catch (err) {
    toast.show("获取详情失败", "error")
  }
}



async function saveMember() {
  // 先把模式存下来：请求过程中别处改动 isEdit 时，提示文案和 payload 仍然一致
  const editing = isEdit.value
  try {
    const res = editing
      ? await updateMember(nowMemberId.value, form)
      : await addMember(form)

    if (res && typeof res.code !== "undefined" && res.code !== 0) {
      toast.show(res.msg || (editing ? "修改失败" : "新增失败"), "error")
      return
    }

    // 新增会连带开一个登录账号，后端把「账号 + 初始密码」写在 msg 里，
    // 直接用后端的提示，前台才能当面把凭据告诉会员。
    toast.show(editing ? "修改成功" : (res.msg || "新增成功"))
    await loadList() // 优先加载数据，再关闭弹窗
    showModal.value = false
  } catch (e) {
    toast.show(editing ? "修改失败" : "新增失败", "error")
  }
}




async function removeMember(item) {
  // 原来是点一下就删，没有二次确认 —— 会员档案还连着打卡、预约、消费记录，
  // 删掉之后这些会一起没，必须让操作者先看清删的是谁。
  const ok = await confirmDialog({
    title: "删除会员",
    tone: "danger",
    message: "该会员的打卡记录、预约记录、消费记录会一并删除，此操作不可恢复。",
    details: [
      { label: "会员", value: item.name },
      { label: "手机号", value: item.phone || "—" },
      { label: "卡类型", value: item.card_type || "—" }
    ],
    confirmText: "删除"
  });
  if (!ok) return;
  try {
    await deleteMember(item.id);
    toast.show("会员已删除");
    await loadList()
  } catch (e) {
    toast.show(e.friendlyMessage || "删除失败", "error")
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
