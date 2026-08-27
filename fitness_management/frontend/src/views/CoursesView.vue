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
      <div class="tabs">
        <button class="tab-btn" :class="{ active: activeTab === 'group' }" type="button" @click="activeTab = 'group'">公共团课</button>
        <button class="tab-btn" :class="{ active: activeTab === 'private' }" type="button" @click="activeTab = 'private'">私教课程</button>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>课程名称</th>
                <th>{{ activeTab === 'group' ? '分类' : '授课教练' }}</th>
                <th>{{ activeTab === 'group' ? '授课教练' : '课时时长' }}</th>
                <th>{{ activeTab === 'group' ? '上课时间' : '课时单价' }}</th>
                <th>{{ activeTab === 'group' ? '人数' : '会员名额' }}</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in currentList" :key="item.id">
                <td>{{ item.name }}</td>
                <td>{{ activeTab === 'group' ? item.category : item.coach }}</td>
                <td>{{ activeTab === 'group' ? item.coach : item.duration }}</td>
                <td>{{ activeTab === 'group' ? item.time : '¥ ' + item.price }}</td>
                <td>{{ activeTab === 'group' ? item.booked + ' / ' + item.max : item.capacity + ' 个' }}</td>
                <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
                <td>
                  <div class="page-actions">
                    <button v-if="canManage" class="btn btn-secondary btn-sm" type="button" @click="toggle(item)">{{ item.status === '已下架' ? '上架' : '下架' }}</button>
                    <button v-if="canManage" class="btn btn-danger btn-sm" type="button" @click="remove(item)">删除</button>
                    <button v-if="!canManage && role === 'coach'" class="btn btn-secondary btn-sm" type="button" @click="openReservation(item)">预约名单</button>
                    <button v-if="!canManage && role === 'member'" class="btn btn-primary btn-sm" type="button" @click="book(item)">预约</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
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
            <div class="field"><label>授课教练</label><input v-model="courseForm.coach" type="text"></div>
            <div class="field"><label>时长</label><input v-model="courseForm.duration" type="text"></div>
            <div class="field"><label>价格</label><input v-model.number="courseForm.price" type="number"></div>
            <div class="field"><label>状态</label><select v-model="courseForm.status"><option>已上架</option><option>已下架</option></select></div>
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
              <thead><tr><th>会员</th><th>手机号</th><th>状态</th></tr></thead>
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
import { computed, reactive, ref } from "vue";
import { useAuth } from "../composables/useAuth";
import { useToast } from "../composables/useToast";
import { groupCourses, privateCourses } from "../data/mock";

const auth = useAuth();
const toast = useToast();
const role = auth.currentRole.value;
const canManage = role === "admin" || role === "reception";
const activeTab = ref("group");
const groupList = ref(groupCourses.map((item) => ({ ...item })));
const privateList = ref(privateCourses.map((item) => ({ ...item })));
const showAdd = ref(false);
const showReservation = ref(false);
const selectedCourse = ref(null);
const courseForm = reactive({
  name: "",
  coach: "",
  duration: "60 分钟",
  price: 0,
  status: "已上架"
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

const currentList = computed(() => activeTab.value === "group" ? groupList.value : privateList.value);
const reservationList = computed(() => {
  if (!selectedCourse.value) return [];
  return [
    { member: "王琳", phone: "13800000001", status: "已预约" },
    { member: "赵敏", phone: "13800000003", status: "已预约" },
    { member: "郑雪", phone: "13800000011", status: "已签到" }
  ];
});

function statusClass(status) {
  if (status === "已上架") return "success";
  if (status === "已满员") return "warn";
  return "muted";
}

function openAdd() {
  showAdd.value = true;
}

function saveCourse() {
  const target = activeTab.value === "group" ? groupList.value : privateList.value;
  target.unshift({
    id: (activeTab.value === "group" ? "G" : "P") + Date.now().toString().slice(-4),
    ...courseForm,
    category: "瑜伽",
    time: "周一 19:00",
    max: 20,
    booked: 0,
    capacity: 10
  });
  showAdd.value = false;
  toast.show("课程已新增");
}

function toggle(item) {
  item.status = item.status === "已下架" ? "已上架" : "已下架";
  toast.show(item.name + " 已" + item.status);
}

function remove(item) {
  const target = activeTab.value === "group" ? groupList.value : privateList.value;
  const index = target.findIndex((row) => row.id === item.id);
  if (index >= 0) {
    target.splice(index, 1);
  }
  toast.show("课程已删除");
}

function openReservation(item) {
  selectedCourse.value = item;
  showReservation.value = true;
}

function book(item) {
  toast.show("预约成功，可在会员个人中心查看");
}
</script>
