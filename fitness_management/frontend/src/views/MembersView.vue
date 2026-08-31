<template>
  <div>
    <transition name="fade">
      <div v-if="toast.message.value" class="toast-banner" :class="toast.type.value">{{ toast.message.value }}</div>
    </transition>

    <div class="page-header">
      <div>
        <h1>{{ isReception ? "会员开卡续费" : "会员管理" }}</h1>
        <p class="page-desc">{{ isReception ? "办理会员开卡、续费，查询消费流水和会员详情。" : "维护会员档案、办卡续费、消费记录和会员明细。" }}</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary" type="button" @click="openAdd">新增会员</button>
      </div>
    </div>

    <div class="panel">
      <div class="panel-body">
        <div class="filter-bar">
          <div class="field">
            <label>关键词</label>
            <input v-model="keyword" type="search" placeholder="会员姓名或手机号">
          </div>
          <div class="field">
            <label>卡状态</label>
            <select v-model="statusFilter">
              <option value="">全部状态</option>
              <option value="正常">正常</option>
              <option value="过期">过期</option>
              <option value="暂停">暂停</option>
            </select>
          </div>
          <div class="field">
            <label>办卡类型</label>
            <select v-model="cardTypeFilter">
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
        <span class="badge info">共 {{ filteredMembers.length }} 条</span>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>会员编号</th><th>姓名</th><th>手机号</th><th>性别</th><th>年龄</th>
                <th>办卡类型</th><th>到期时间</th><th>余额</th><th>卡状态</th><th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredMembers" :key="item.id">
                <td>{{ item.id }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.phone }}</td>
                <td>{{ item.gender }}</td>
                <td>{{ item.age }}</td>
                <td>{{ item.card_type }}</td>
                <td>{{ item.card_expire }}</td>
                <td>¥ {{ item.balance.toLocaleString("zh-CN") }}</td>
                <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
                <td>
                  <div class="page-actions">
                    <button class="btn btn-secondary btn-sm" type="button" @click="renew(item)">续费</button>
                    <button class="btn btn-danger btn-sm" type="button" @click="removeMember(item)">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="modal-mask" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">新增会员</h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showModal = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field"><label>姓名</label><input v-model="form.name" type="text"></div>
            <div class="field"><label>手机号</label><input v-model="form.phone" type="text"></div>
            <div class="field"><label>性别</label><select v-model="form.gender"><option>男</option><option>女</option></select></div>
            <div class="field"><label>年龄</label><input v-model="form.age" type="number"></div>
            <div class="field"><label>办卡类型</label><select v-model="form.card_type"><option>月卡</option><option>季卡</option><option>年卡</option><option>次卡</option></select></div>
            <div class="field"><label>到期时间</label><input v-model="form.card_expire" type="date"></div>
            <div class="field"><label>余额</label><input v-model="form.balance" type="number"></div>
            <div class="field"><label>状态</label><select v-model="form.status"><option>正常</option><option>过期</option><option>暂停</option></select></div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showModal = false">取消</button>
          <button class="btn btn-primary" type="button" @click="saveMember">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useAuth } from "../composables/useAuth";
import { useToast } from "../composables/useToast";
import { members } from "../data/mock";
import {addMember, deleteMember, getMemberList, renewMember} from "../api/member.js";
import {onMounted} from "vue";
import {useRouter} from "vue-router";
const router = useRouter();

const auth = useAuth();
const toast = useToast();
const list = ref([]);
const keyword = ref("");
const statusFilter = ref("");
const cardTypeFilter = ref("");
const showModal = ref(false);
const form = reactive({
  name: "",
  gender: "",
  phone: "",
  age: 25,
  card_type: "月卡",
  card_start: "",
  card_expire: "",
  balance: 0,
  status: "正常",
  remark:''
});
const c_renew = ref({
  member_id:'',
  renew:0
})
form.card_start=String(Number(form.card_expire))
const isReception = computed(() => auth.currentRole.value === "reception");

const filteredMembers = computed(() => {
  return list.value.filter((item) => {
    const matchKeyword = !keyword.value || item.name.includes(keyword.value) || item.phone.includes(keyword.value);
    const matchStatus = !statusFilter.value || item.status === statusFilter.value;
    const matchCard = !cardTypeFilter.value || item.card_type === cardTypeFilter.value;
    return matchKeyword && matchStatus && matchCard;
  });
});
onMounted(async () => {
  let res = await getMemberList();
  list.value=res.data
  console.log(list.value)
})

function statusClass(status) {
  if (status === "正常") return "success";
  if (status === "过期") return "danger";
  return "warn";
}

function openAdd() {
  showModal.value = true;
}

async function saveMember() {
  let res = await addMember(form);
  console.log(res)
  showModal.value = false;
  toast.show("会员已创建");
  let res2 = await getMemberList();
  list.value=res2.data
}

async function renew(item) {
  c_renew.id=item.id
  c_renew.renew=100
  let res = await renewMember(c_renew);
  if (res.code===0){
    console.log(res)
  toast.show(item.name + " 续费成功");
  }else{
    toast.show(item.name + " 续费失败");
  }
  let res2 = await getMemberList();
  list.value=res2.data

}

async function removeMember(item) {
  let res = await deleteMember(item.id);
  console.log(res)
  toast.show("会员已删除");
  let res2 = await getMemberList();
  list.value=res2.data
}
</script>
