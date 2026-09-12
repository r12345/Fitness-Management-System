<template>
  <div class="login-page">
    <section class="login-visual">
      <div>
        <div class="sidebar-brand" style="padding: 0;">
          <span class="brand-mark">健</span>
          <div>
            <div class="brand-name">健身管理系统</div>
            <div class="brand-sub">Vue3 前后端分离版</div>
          </div>
        </div>
        <h1>{{ visualTitle }}</h1>
      </div>
      <p>{{ visualDesc }}</p>
    </section>

    <section class="login-form-side">
      <div class="login-card">
        <div class="auth-tabs">
          <button
            type="button"
            class="auth-tab"
            :class="{ active: mode === 'login' }"
            @click="switchMode('login')"
          >
            账号登录
          </button>
          <button
            type="button"
            class="auth-tab"
            :class="{ active: mode === 'register' }"
            @click="switchMode('register')"
          >
            注册新账号
          </button>
        </div>

        <p class="page-desc" style="margin: 0 0 20px;">
          {{ mode === "login" ? "选择角色并输入账号密码" : "填写信息创建账号，注册后即可登录" }}
        </p>

        <div
          v-if="notice"
          class="login-notice"
          :class="notice.type === 'success' ? 'login-success' : 'login-error'"
        >
          {{ notice.text }}
        </div>

        <!-- ============ 登录 ============ -->
        <form v-if="mode === 'login'" @submit.prevent="handleLogin">
          <div class="role-grid">
            <button
              v-for="item in LOGIN_ROLES"
              :key="item.value"
              type="button"
              class="role-option"
              :class="{ active: loginForm.role === item.value }"
              @click="selectLoginRole(item.value)"
            >
              <span class="role-option-icon">{{ item.icon }}</span>
              <span>
                <strong>{{ item.label }}</strong>
                <small class="page-desc" style="display: block;">{{ item.desc }}</small>
              </span>
            </button>
          </div>

          <div class="login-role-tip">{{ currentRoleTip }}</div>

          <div class="field" :class="{ 'has-error': errors.username }" style="margin-bottom: 14px;">
            <label for="login-username">账号</label>
            <input
              id="login-username"
              v-model.trim="loginForm.username"
              type="text"
              placeholder="请输入账号"
              autocomplete="username"
            >
            <span v-if="errors.username" class="field-error">{{ errors.username }}</span>
          </div>

          <div class="field" :class="{ 'has-error': errors.password }" style="margin-bottom: 18px;">
            <label for="login-password">密码</label>
            <input
              id="login-password"
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              autocomplete="current-password"
            >
            <span v-if="errors.password" class="field-error">{{ errors.password }}</span>
          </div>

          <button class="btn btn-primary" type="submit" style="width: 100%;" :disabled="loading">
            {{ loading ? "正在登录..." : "登录系统" }}
          </button>

          <div class="login-tip">
            没有账号？点击上方「注册新账号」创建；预置账号的密码需与数据库一致。
          </div>

          <div class="auth-switch">
            还没有账号？
            <button type="button" class="link-btn" @click="switchMode('register')">立即注册</button>
          </div>
        </form>

        <!-- ============ 注册 ============ -->
        <form v-else @submit.prevent="handleRegister">
          <div class="role-grid">
            <button
              v-for="item in REGISTER_ROLES"
              :key="item.value"
              type="button"
              class="role-option"
              :class="{ active: registerForm.role === item.value }"
              @click="selectRegisterRole(item.value)"
            >
              <span class="role-option-icon">{{ item.icon }}</span>
              <span>
                <strong>{{ item.label }}</strong>
                <small class="page-desc" style="display: block;">{{ item.desc }}</small>
              </span>
            </button>
          </div>

          <div class="login-role-tip">{{ registerRoleTip }}</div>

          <div class="form-grid">
            <div class="field full" :class="{ 'has-error': errors.username }">
              <label for="reg-username">账号</label>
              <input
                id="reg-username"
                v-model.trim="registerForm.username"
                type="text"
                placeholder="3-20 位字母、数字或下划线"
                autocomplete="username"
              >
              <span v-if="errors.username" class="field-error">{{ errors.username }}</span>
            </div>

            <div class="field" :class="{ 'has-error': errors.name }">
              <label for="reg-name">姓名</label>
              <input
                id="reg-name"
                v-model.trim="registerForm.name"
                type="text"
                placeholder="请输入真实姓名"
                autocomplete="name"
              >
              <span v-if="errors.name" class="field-error">{{ errors.name }}</span>
            </div>

            <div class="field" :class="{ 'has-error': errors.phone }">
              <label for="reg-phone">手机号</label>
              <input
                id="reg-phone"
                v-model.trim="registerForm.phone"
                type="tel"
                maxlength="11"
                placeholder="11 位手机号"
                autocomplete="tel"
              >
              <span v-if="errors.phone" class="field-error">{{ errors.phone }}</span>
            </div>

            <div class="field" :class="{ 'has-error': errors.password }">
              <label for="reg-password">密码</label>
              <input
                id="reg-password"
                v-model="registerForm.password"
                type="password"
                placeholder="6-20 位"
                autocomplete="new-password"
              >
              <span v-if="errors.password" class="field-error">{{ errors.password }}</span>
            </div>

            <div class="field" :class="{ 'has-error': errors.confirmPassword }">
              <label for="reg-confirm">确认密码</label>
              <input
                id="reg-confirm"
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                autocomplete="new-password"
              >
              <span v-if="errors.confirmPassword" class="field-error">{{ errors.confirmPassword }}</span>
            </div>
          </div>

          <button
            class="btn btn-primary"
            type="submit"
            style="width: 100%; margin-top: 18px;"
            :disabled="loading"
          >
            {{ loading ? "正在提交..." : "注册账号" }}
          </button>

          <div class="login-tip">
            账号不可重复；会员/教练/前台注册后会自动生成对应的档案记录。
          </div>

          <div class="auth-switch">
            已有账号？
            <button type="button" class="link-btn" @click="switchMode('login')">返回登录</button>
          </div>
        </form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuth, homeOfRole } from "../composables/useAuth";
import { login, register, isRegisterSuccess, pickMessage } from "../api/user.js";

const router = useRouter();
const route = useRoute();
const auth = useAuth();

/** 登录可选角色 */
const LOGIN_ROLES = [
  { value: "admin", label: "超级管理员", icon: "管", desc: "全模块运营与权限管理" },
  { value: "reception", label: "前台运营", icon: "前", desc: "开卡、续费、预约与报修" },
  { value: "coach", label: "健身教练", icon: "教", desc: "排课、学员与训练计划" },
  { value: "member", label: "普通会员", icon: "会", desc: "预约、打卡与训练记录" }
];

/**
 * 注册可选角色。
 * 只开放 register_user 会同步建档的三个角色，不提供 admin，
 * 避免任何人自助创建管理员账号。
 */
const REGISTER_ROLES = [
  { value: "member", label: "普通会员", icon: "会", desc: "预约、打卡与训练记录" },
  { value: "coach", label: "健身教练", icon: "教", desc: "排课、学员与训练计划" },
  { value: "reception", label: "前台运营", icon: "前", desc: "开卡、续费与预约处理" }
];

const loginForm = reactive({
  role: "admin",
  username: "",
  password: ""
});

const registerForm = reactive({
  role: "member",
  username: "",
  name: "",
  phone: "",
  password: "",
  confirmPassword: ""
});

const loading = ref(false);
const errors = ref({});

/** 退出登录后由 AppLayout 写入提示，读一次就清掉，避免反复出现 */
const pendingNotice = sessionStorage.getItem("gym_login_notice");
if (pendingNotice) {
  sessionStorage.removeItem("gym_login_notice");
}

const notice = ref(pendingNotice ? { type: "success", text: pendingNotice } : null);

/** 支持直接访问 /register 进入注册模式 */
const mode = ref(route.path === "/register" ? "register" : "login");

// 浏览器前进/后退切换 /login 与 /register 时同步模式（两个路由共用本组件）
watch(() => route.path, (path) => {
  const next = path === "/register" ? "register" : "login";
  if (next !== mode.value) {
    mode.value = next;
    errors.value = {};
  }
});

const visualTitle = computed(() =>
  mode.value === "login"
    ? "让日常运营、课程预约和会员服务在一个平台高效完成"
    : "几秒钟创建账号，立即开始使用健身管理系统"
);

const visualDesc = computed(() =>
  mode.value === "login"
    ? "超级管理员、前台运营、健身教练、普通会员四种角色分别进入对应工作台。"
    : "注册会员可直接预约课程、打卡并查看训练计划；教练与前台账号注册后即可进入对应工作台。"
);

function roleTip(list, value) {
  const current = list.find((item) => item.value === value);
  return current ? `当前选择：${current.label}，${current.desc}` : "";
}

const currentRoleTip = computed(() => roleTip(LOGIN_ROLES, loginForm.role));
const registerRoleTip = computed(() => roleTip(REGISTER_ROLES, registerForm.role));

function switchMode(next) {
  if (mode.value === next) return;
  mode.value = next;
  errors.value = {};
  notice.value = null;
  // 用 replace 同步地址栏，刷新后仍停留在当前模式
  router.replace(next === "register" ? "/register" : "/login");
}

function selectLoginRole(value) {
  loginForm.role = value;
  errors.value = { ...errors.value, username: "", password: "" };
}

function selectRegisterRole(value) {
  registerForm.role = value;
}

/** 只做提交前的必填/格式校验，业务校验交后端 */
function validateLogin() {
  const next = {};
  if (!loginForm.username) next.username = "请输入账号";
  if (!loginForm.password) next.password = "请输入密码";
  errors.value = next;
  return Object.keys(next).length === 0;
}

function validateRegister() {
  const next = {};
  const form = registerForm;

  if (!form.username) {
    next.username = "请输入账号";
  } else if (!/^[A-Za-z0-9_]{3,20}$/.test(form.username)) {
    next.username = "账号为 3-20 位字母、数字或下划线";
  }

  if (!form.name) {
    next.name = "请输入姓名";
  } else if (form.name.length > 20) {
    next.name = "姓名不超过 20 个字符";
  }

  if (!form.phone) {
    next.phone = "请输入手机号";
  } else if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    next.phone = "手机号格式不正确";
  }

  if (!form.password) {
    next.password = "请输入密码";
  } else if (form.password.length < 6) {
    next.password = "密码至少 6 位";
  } else if (form.password.length > 20) {
    next.password = "密码不超过 20 位";
  }

  if (!form.confirmPassword) {
    next.confirmPassword = "请再次输入密码";
  } else if (form.confirmPassword !== form.password) {
    next.confirmPassword = "两次输入的密码不一致";
  }

  errors.value = next;
  return Object.keys(next).length === 0;
}

/** 登录后的落地页：优先回跳来时的页面，否则按角色首页 */
function resolveLanding(role) {
  const redirect = route.query.redirect;
  if (typeof redirect === "string" && redirect.startsWith("/") && !redirect.startsWith("//")) {
    return redirect;
  }
  // 后端返回的 home 固定是 /dashboard，对教练和会员并不合适，这里按角色自行决定
  return homeOfRole(role);
}

async function handleLogin() {
  notice.value = null;
  if (loading.value || !validateLogin()) return;

  loading.value = true;
  try {
    const res = await login(loginForm.role, loginForm.username, loginForm.password);
    if (res && res.code === 0) {
      const data = res.data || {};
      auth.setSession(data);
      await router.replace(resolveLanding(data.role));
    } else {
      notice.value = { type: "error", text: pickMessage(res, "账号或密码错误") };
    }
  } catch (error) {
    notice.value = { type: "error", text: error.message || "登录失败，请稍后重试" };
  } finally {
    loading.value = false;
  }
}

async function handleRegister() {
  notice.value = null;
  if (loading.value || !validateRegister()) return;

  loading.value = true;
  try {
    const res = await register({
      username: registerForm.username,
      password: registerForm.password,
      role: registerForm.role,
      name: registerForm.name,
      phone: registerForm.phone
    });

    if (isRegisterSuccess(res)) {
      // 回填登录表单，省去重新输入
      loginForm.role = registerForm.role;
      loginForm.username = registerForm.username;
      loginForm.password = "";
      resetRegisterForm();
      switchMode("login");
      notice.value = { type: "success", text: "注册成功，请使用新账号登录" };
    } else {
      notice.value = { type: "error", text: pickMessage(res, "注册失败，请稍后重试") };
    }
  } catch (error) {
    notice.value = { type: "error", text: error.message || "注册失败，请稍后重试" };
  } finally {
    loading.value = false;
  }
}

function resetRegisterForm() {
  registerForm.username = "";
  registerForm.name = "";
  registerForm.phone = "";
  registerForm.password = "";
  registerForm.confirmPassword = "";
  errors.value = {};
}
</script>
