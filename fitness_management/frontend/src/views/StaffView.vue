<template>
  <div>
    <transition name="fade">
      <div v-if="toast.message" class="toast-banner" :class="toast.type">{{ toast.message }}</div>
    </transition>

    <div class="page-header">
      <div>
        <h1>运营人员</h1>
        <p class="page-desc">
          前台运营人员的档案与登录账号，由超级管理员统一建立。
        </p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary" type="button" @click="openAdd">新增运营人员</button>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <h2 class="panel-title">运营人员列表</h2>
        <span>
          共 {{ list.length }} 人<template v-if="adoptCount">，其中 {{ adoptCount }} 人未建档</template>
        </span>
      </div>
      <div class="panel-body no-padding">
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>编号</th>
                <th>姓名</th>
                <th>联系电话</th>
                <th>登录账号</th>
                <th>薪资</th>
                <th>入职时间</th>
                <th>状态</th>
                <th>备注</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!list.length">
                <td colspan="9" style="text-align:center;color:#999;">
                  暂无运营人员，点右上角「新增运营人员」建立
                </td>
              </tr>
              <!-- 列表是「账号 ∪ 档案」：只有账号没档案的历史遗留行 id 为空，key 用 user_id 兜底 -->
              <tr v-for="item in list" :key="item.id ?? `u${item.user_id}`">
                <td>{{ item.id ?? '-' }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.phone || '-' }}</td>
                <!-- 账号名要显示出来：管理员得当面告诉本人拿什么登录 -->
                <td>
                  <span class="badge" :class="item.has_account ? 'success' : 'danger'">
                    {{ item.has_account ? '已开通' : '无账号' }}
                  </span>
                  <span v-if="item.username" style="margin-left:6px;color:#555;">{{ item.username }}</span>
                </td>
                <td>{{ item.salary ?? '-' }}</td>
                <td>{{ item.hire_date || '-' }}</td>
                <td>
                  <span v-if="item.has_profile" class="badge" :class="statusClass(item.status)">
                    {{ item.status }}
                  </span>
                  <span v-else class="badge muted">未建档</span>
                </td>
                <td>{{ item.remark || '-' }}</td>
                <td>
                  <div class="page-actions">
                    <button
                      v-if="!item.has_profile"
                      class="btn btn-secondary btn-sm"
                      type="button"
                      @click="openAdopt(item)"
                    >
                      补建档案
                    </button>
                    <button
                      v-if="item.has_profile"
                      class="btn btn-danger btn-sm"
                      type="button"
                      @click="removeStaff(item)"
                    >
                      删除
                    </button>
                    <button
                      v-else
                      class="btn btn-danger btn-sm"
                      type="button"
                      @click="removeAccount(item)"
                    >
                      删除账号
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 新增运营人员弹窗；「补建档案」复用同一个弹窗，只是预填已有账号的信息 -->
    <div v-if="showModal" class="modal-mask" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3 class="panel-title">
            {{ adoptTarget ? `为「${adoptTarget.name}」补建档案` : '新增运营人员' }}
          </h3>
          <button class="btn btn-secondary btn-sm" type="button" @click="showModal = false">关闭</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field">
              <label>姓名</label>
              <input v-model="form.name" type="text">
            </div>
            <div class="field">
              <label>联系电话</label>
              <input v-model="form.phone" type="text" placeholder="同时作为登录账号">
            </div>
            <div class="field">
              <label>薪资</label>
              <input v-model.number="form.salary" type="number" step="0.01">
            </div>
            <div class="field">
              <label>入职时间</label>
              <input v-model="form.hire_date" type="date">
            </div>
            <div class="field">
              <label>状态</label>
              <select v-model="form.status">
                <option value="在职">在职</option>
                <option value="休假">休假</option>
                <option value="离职">离职</option>
              </select>
            </div>
            <div class="field">
              <label>备注</label>
              <input v-model="form.remark" type="text">
            </div>
          </div>
          <!-- 账号由系统开：手机号当账号名，初始密码统一 123456，
               本人登录后可在右上角「修改密码」自行修改。 -->
          <p v-if="adoptTarget" class="field-hint">
            这个手机号下已经有登录账号「{{ adoptTarget.username }}」，保存后直接沿用，
            不会新建账号、也不会重置它的密码。
          </p>
          <p v-else class="field-hint">
            保存后会同时创建登录账号：账号为上面填写的手机号，初始密码 123456。
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="showModal = false">取消</button>
          <button class="btn btn-primary" type="button" @click="saveStaff">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { createStaff, deleteStaff, deleteStaffAccount, getStaffList } from "../api/reception.js";
import { useToast } from "../composables/useToast";
import { confirmDialog } from "../composables/useConfirm.js";

const toast = useToast();
const list = ref([]);
const showModal = ref(false);
// 非空表示当前弹窗是「给这个已有账号补建档案」，而不是新建
const adoptTarget = ref(null);

// 只有账号、还没建档案的人：历史遗留，管理员的视线里不能是空的
const adoptCount = computed(() => list.value.filter((item) => !item.has_profile).length);

const form = reactive({
  name: "",
  phone: "",
  salary: null,
  hire_date: "",
  status: "在职",
  remark: ""
});

/** 在职绿、休假黄、离职灰，与教练管理页同一套口径 */
function statusClass(status) {
  if (status === "在职") return "success";
  if (status === "休假") return "warn";
  return "muted";
}

async function loadList() {
  try {
    const res = await getStaffList();
    list.value = res.data || [];
  } catch (err) {
    toast.show(err.friendlyMessage || "加载运营人员失败", "error");
  }
}

/** 新增：清空表单，走「开新账号」那条路 */
function openAdd() {
  adoptTarget.value = null;
  form.name = "";
  form.phone = "";
  form.salary = null;
  form.hire_date = new Date().toISOString().split("T")[0];
  form.status = "在职";
  form.remark = "";
  showModal.value = true;
}

/** 补建档案：把已有账号的姓名/电话预填进来，保存时后端会认领原账号 */
function openAdopt(item) {
  adoptTarget.value = item;
  form.name = item.name || "";
  form.phone = item.phone || "";
  form.salary = null;
  form.hire_date = new Date().toISOString().split("T")[0];
  form.status = "在职";
  form.remark = "";
  showModal.value = true;
}

async function saveStaff() {
  if (!form.name.trim()) {
    toast.show("请填写姓名", "error");
    return;
  }
  if (!form.phone.trim()) {
    toast.show("请填写联系电话（同时作为登录账号）", "error");
    return;
  }
  if (!form.hire_date) {
    toast.show("请选择入职时间", "error");
    return;
  }
  try {
    const res = await createStaff({
      name: form.name.trim(),
      phone: form.phone.trim(),
      salary: form.salary,
      hire_date: form.hire_date,
      status: form.status,
      remark: form.remark.trim()
    });
    // 后端把账号情况写在 msg 里：新建的报「初始密码 123456」，
    // 认领已有账号的报「沿用原账号、密码未改动」，管理员要照这个转告本人
    toast.show(res.msg || "运营人员已新增");
    showModal.value = false;
    await loadList();
  } catch (err) {
    toast.show(err.friendlyMessage || "新增失败，请重试", "error");
  }
}

async function removeStaff(item) {
  const ok = await confirmDialog({
    title: "删除运营人员",
    tone: "danger",
    message: "该运营人员的登录账号会一并删除，删除后本人将无法登录系统。\n此操作不可恢复。",
    details: [
      { label: "姓名", value: item.name },
      { label: "联系电话", value: item.phone || "—" }
    ],
    confirmText: "删除"
  });
  if (!ok) return;
  try {
    const res = await deleteStaff(item.id);
    toast.show(res.msg || "已删除");
    await loadList();
  } catch (err) {
    toast.show(err.friendlyMessage || "删除失败", "error");
  }
}

/** 删除「未建档」的裸账号：走的是账号路由，不是档案编号 */
async function removeAccount(item) {
  const ok = await confirmDialog({
    title: "删除运营账号",
    tone: "danger",
    message: "该账号还没有人员档案，删除后本人将无法登录系统。\n此操作不可恢复。",
    details: [
      { label: "账号", value: item.username || "—" },
      { label: "姓名", value: item.name || "—" }
    ],
    confirmText: "删除"
  });
  if (!ok) return;
  try {
    const res = await deleteStaffAccount(item.user_id);
    toast.show(res.msg || "已删除");
    await loadList();
  } catch (err) {
    toast.show(err.friendlyMessage || "删除失败", "error");
  }
}

onMounted(loadList);
</script>
