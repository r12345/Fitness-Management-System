<template>
  <div>
    <div class="page-header">
      <div>
        <h1>前台运营工作台</h1>
        <p class="page-desc">处理会员开卡、续费、课程预约和器材报修登记。</p>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard
        v-for="(item, index) in data"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :unit="item.unit"
        :icon="['开', '约', '修', '收'][index]"
        :tone="index === 2 ? 'warn' : ''"
      />
    </div>

    <div class="course-cards" style="margin-bottom: 20px;">
      <router-link
        v-for="item in data1"
        :key="item.path"
        class="course-card"
        :to="item.path"
      >
        <div class="course-card-top">
          <h3>{{ item.title }}</h3>
          <span class="badge" :class="item.tone">{{ item.badge }}</span>
        </div>
        <div class="course-card-meta">
          <span>{{ item.desc }}</span>
        </div>
      </router-link>
    </div>

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">今日业务动态</h2>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>时间</th><th>操作人</th><th>会员或器材</th><th>内容</th><th>支付方式</th></tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in data2" :key="index">
                <td>{{ item.time }}</td>
                <td>{{ item.operator }}</td>
                <td>{{ item.target }}</td>
                <td>{{ item.content }}</td>
                <td>
                  {{ item.pay_method}}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import StatCard from "../components/StatCard.vue";
import {get_recent_business_log, get_summary} from "../api/reception.js";
import {onMounted} from "vue";
import {ref} from "vue";
const data = ref([
    {label:'今日开卡',value:null,unit:'人'},
    {label:'待处理预约',value:null,unit:'条'},
    {label:'待报修器材',value:null,unit:'台'},
    {label:'今日消费',value:null,unit:'元'},
])

const data1 = ref([
  { title: "会员开卡续费", desc: "新增会员、卡种配置、续费与消费记录", path: "/members", badge: "办理中", tone: "success" },
    { title: "课程预约处理", desc: "查看预约、处理冲突、确认签到", path: "/courses", badge: "待处理 ", tone: "info" },
    { title: "器材报修登记", desc: "登记故障、跟进维修、记录保养", path: "/equipment", badge: "待报修 ", tone: "warn" }
])

const data2 = ref(
    []
)

async function get_log(){
  const res = await get_recent_business_log()
  data2.value = res.data.items
}

async function get_sum(){
  const res = await get_summary();
  data.value[0].value = res.data.today_new_members
  data.value[1].value = res.data.pending_appointments
  data.value[2].value = res.data.pending_repairs
  data.value[3].value = res.data.today_revenue
}
onMounted(async()=>{
  await get_sum();
  await get_log()
})
</script>
