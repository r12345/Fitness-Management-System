<template>
  <div class="app-layout">
    <aside class="sidebar" :class="{ open: menuOpen }">
      <div class="sidebar-brand">
        <span class="brand-mark">健</span>
        <div>
          <div class="brand-name">健身管理系统</div>
          <div class="brand-sub">前后端分离版</div>
        </div>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-section">
          <div class="nav-section-title">当前角色模块</div>
          <router-link
            v-for="item in navItems"
            :key="item.path"
            class="nav-link"
            :to="item.path"
          >
            {{ item.label }}
          </router-link>
        </div>
      </nav>
      <div class="sidebar-footer">
        <div>当前日期：{{ today }}</div>
        <div>© {{ year }} 健身管理系统</div>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div class="topbar-left">
          <button class="btn btn-secondary mobile-menu-btn" type="button" @click="menuOpen = !menuOpen">菜单</button>
          <div class="topbar-title">{{ topbarTitle }}</div>
        </div>
        <div class="topbar-right">
          <div class="user-chip">
            <span>{{ useStore.role_name }} · {{ useStore.role }}</span>
          </div>
          <button class="btn btn-secondary btn-sm" type="button" @click="handleLogout">退出</button>
        </div>
      </header>

      <div class="page-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth";
import {useUserStore} from "../stores/user.js";
const useStore=useUserStore()
const route = useRoute();
const router = useRouter();
const auth = useAuth();
const menuOpen = ref(false);
const navItems = computed(() => MODULES[useStore.role]);
const MODULES = {
  admin: [
    { path: "/dashboard", label: "数据大盘" },
    { path: "/reception", label: "前台运营工作台" },
    { path: "/members", label: "会员管理" },
    { path: "/coaches", label: "教练管理" },
    { path: "/courses", label: "课程与预约" },
    { path: "/equipment", label: "器材管理" },
    { path: "/system", label: "系统配置" },
    { path: "/member", label: "会员个人中心" },
    { path: "/coach", label: "教练工作台" },
      { path: "/appointments", label: "预约" }
  ],
  reception: [
    { path: "/reception", label: "前台工作台" },
    { path: "/members", label: "会员开卡续费" },
    { path: "/courses", label: "课程" },
    { path: "/equipment", label: "器材报修" },
    { path: "/dashboard", label: "运营概览" },
    { path: "/appointments", label: "预约" }
  ],
  coach: [
    { path: "/coach", label: "我的工作台" },
    { path: "/courses", label: "课程中心" },
    { path: "/appointments", label: "预约" }
  ],
  member: [
    { path: "/member", label: "个人中心" },
    { path: "/courses", label: "课程" }
  ]
};

const today = new Date().toLocaleDateString("zh-CN");
const year = new Date().getFullYear() + "年";

const ROLE_PAGE_TITLES = {
  reception: {
    "/dashboard": "运营概览",
    "/members": "会员开卡续费",
    "/courses": "预约处理",
    "/equipment": "器材报修"
  },
  coach: {
    "/courses": "课程中心"
  },
  member: {
    "/courses": "预约课程"
  }
};

const topbarTitle = computed(() => {
  const titles = ROLE_PAGE_TITLES[useStore.role];
  if (titles && titles[route.path]) {
    return titles[route.path];
  }
  return route.meta.title;
});

function handleLogout() {
  useStore.setToken('');
  router.replace("/login");
}
</script>
