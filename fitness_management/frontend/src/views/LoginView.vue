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
        <h1>让日常运营、课程预约和会员服务在一个平台高效完成</h1>
      </div>
      <p>超级管理员、前台运营、健身教练、普通会员四种角色分别进入对应工作台。</p>
    </section>

    <section class="login-form-side">
      <form class="login-card" @submit.prevent="handleLogin">
        <h2 style="margin: 0 0 4px;">账号登录</h2>
        <p class="page-desc" style="margin-bottom: 22px;">选择角色并输入账号密码</p>

        <div class="role-grid">
          <button
            v-for="item in roles"
            :key="item.value"
            type="button"
            class="role-option"
            :class="{ active: form.role === item.value }"
            @click="form.role = item.value"
          >
            <span class="role-option-icon">{{ item.icon }}</span>
            <span>
              <strong>{{ item.label }}</strong>
              <small class="page-desc" style="display: block;">{{ item.desc }}</small>
            </span>
          </button>
        </div>

        <div class="login-role-tip">{{ currentRoleTip }}</div>
        <div v-if="notice" class="login-error">{{ notice }}</div>

        <div class="field" style="margin-bottom: 14px;">
          <label for="username">账号</label>
          <input id="username" v-model="form.username" type="text" placeholder="请输入账号">
        </div>
        <div class="field" style="margin-bottom: 18px;">
          <label for="password">密码</label>
          <input id="password" v-model="form.password" type="password" placeholder="请输入密码">
        </div>

        <button class="btn btn-primary" type="submit" style="width: 100%;" :disabled="loading">
          {{ loading ? "正在登录..." : "登录系统" }}
        </button>

        <div class="login-tip">
          演示环境：任意角色均可使用 admin / 123456 登录。
        </div>
      </form>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth";
import { useUserStore } from "../stores/user";

import { login} from "../api/user.js";
const router = useRouter();
const auth = useAuth();
const userStore = useUserStore();
const roles = [
  { value: "admin", label: "超级管理员", icon: "管", desc: "全模块运营与权限管理" },
  { value: "reception", label: "前台运营", icon: "前", desc: "开卡、续费、预约与报修" },
  { value: "coach", label: "健身教练", icon: "教", desc: "排课、学员与训练计划" },
  { value: "member", label: "普通会员", icon: "会", desc: "预约、打卡与训练记录" }
];

const form = reactive({
  role: "admin",
  username: "",
  password: ""
});

const loading = ref(false);
const notice = ref(sessionStorage.getItem("gym_login_notice") || "");

const currentRoleTip = computed(() => {
  const current = roles.find((item) => item.value === form.role);
  return current ? "当前选择：" + current.label + "，" + current.desc : "";
});

const handleLogin= async()=> {
  let res = await login(form.role,form.username,form.password)
  console.log(res)
  if (res.code === 0) {
    console.log('登录成功')
    userStore.setToken(res.data.token);
    userStore.setRole(res.data.role);
    userStore.setRoleName(res.data.role_name);
    router.push('/dashboard');
  } else {
    notice.value = res.message;
  }

  }

</script>
