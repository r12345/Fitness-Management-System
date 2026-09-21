<template>
  <div class="app-layout" :class="{ collapsed: collapsed }">
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

    <div class="sidebar-backdrop" :class="{ open: menuOpen }" @click="menuOpen = false"></div>

    <main class="main">
      <header class="topbar">
        <div class="topbar-left">
          <button
            class="btn btn-secondary menu-btn"
            type="button"
            :aria-label="menuExpanded ? '收起菜单' : '展开菜单'"
            :aria-expanded="menuExpanded"
            @click="toggleMenu"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
              <path
                d="M4 6h16M4 12h16M4 18h16"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              />
            </svg>
          </button>
          <div class="topbar-title">{{ topbarTitle }}</div>
        </div>
        <div class="topbar-right">
          <div class="user-chip">
            <span>{{ useStore.role_name }} · {{ roleLabel }}</span>
          </div>
          <!-- 修改密码对四个角色都开放：新增教练/运营/会员时开的是初始账号
               （初始密码 123456），本人登录后要能自己改掉。 -->
          <button class="btn btn-secondary btn-sm" type="button" @click="showPasswordDialog = true">
            修改密码
          </button>
          <button class="btn btn-secondary btn-sm" type="button" @click="handleLogout">退出</button>
        </div>
      </header>

      <transition name="fade">
        <div v-if="toast.message" class="toast-banner" :class="toast.type">{{ toast.message }}</div>
      </transition>

      <div class="page-content">
        <router-view />
      </div>
    </main>

    <PasswordDialog v-model:open="showPasswordDialog" @saved="onPasswordSaved" />

    <!--
      AI 助手悬浮球挂在这里而不是某个页面里：它是 fixed 定位的，跟着布局走就等于
      登录后的每个页面都常驻，且切换路由时不会被卸载（位置、加载状态都能保住）。
    -->
    <AgentFab />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import AgentFab from "./AgentFab.vue";
import PasswordDialog from "./PasswordDialog.vue";
import { useAuth } from "../composables/useAuth";
import { useCozeAgent } from "../composables/useCozeAgent";
import { useToast } from "../composables/useToast";
import { useUserStore } from "../stores/user.js";

const useStore = useUserStore();
const route = useRoute();
const router = useRouter();
const auth = useAuth();
const toast = useToast();
// 只用到销毁：AI 助手是单例、且构造时就把「谁的令牌」固定下来了
const { destroyAgent } = useCozeAgent();

// 修改密码弹窗（顶栏入口，四个角色通用）
const showPasswordDialog = ref(false);

/** 弹窗关掉后由这里统一提示：提示条挂在布局上，不受弹窗关闭影响 */
function onPasswordSaved(message) {
  toast.show(message || "密码已修改");
}

/**
 * 侧栏有两种形态，左上角那个按钮要同时管住它们：
 * - 宽屏（>860px）：侧栏常驻，按钮切换「折叠 / 展开」
 * - 窄屏（≤860px）：侧栏是抽屉，按钮切换「拉开 / 收起」
 *
 * 原来按钮只改 menuOpen，而宽屏下侧栏本来就是展开的、
 * 遮罩又只在窄屏媒体查询里定义 → 宽屏点它毫无反应，等于死按钮。
 */
const NARROW_QUERY = "(max-width: 860px)";
const isNarrow = ref(false);
const menuOpen = ref(false);
const collapsed = ref(false);
let mediaQuery = null;

function syncNarrow(event) {
  isNarrow.value = event.matches;
  // 切换宽度时把另一种形态的状态收干净，避免折叠与抽屉互相顶掉
  if (isNarrow.value) {
    collapsed.value = false;
  } else {
    menuOpen.value = false;
  }
}

onMounted(() => {
  mediaQuery = window.matchMedia(NARROW_QUERY);
  syncNarrow(mediaQuery);
  mediaQuery.addEventListener("change", syncNarrow);
});

onBeforeUnmount(() => {
  if (mediaQuery) mediaQuery.removeEventListener("change", syncNarrow);
});

function toggleMenu() {
  if (isNarrow.value) {
    menuOpen.value = !menuOpen.value;
  } else {
    collapsed.value = !collapsed.value;
  }
}

/** 菜单当前是否是展开状态，仅用于 aria 提示 */
const menuExpanded = computed(() => (isNarrow.value ? menuOpen.value : !collapsed.value));

/**
 * 侧栏菜单项。
 * 手写的 NAV_ORDER 负责顺序和各角色的专属叫法，
 * 再按路由表补齐漏写的页面：只靠手写列表，一旦新增页面或改了 meta.roles，
 * 就会出现「这个角色明明能进、菜单里却没有入口」这种对不上的问题。
 */
const navItems = computed(() => {
  const role = useStore.role;
  if (!role) return [];

  const seen = new Set();
  const items = [];

  (NAV_ORDER[role] || []).forEach((item) => {
    const allow = router.resolve(item.path).meta.roles;
    // 路由表说不允许，手写列表里也不能硬塞
    if (allow && !allow.includes(role)) return;
    if (seen.has(item.path)) return;
    seen.add(item.path);
    items.push({ path: item.path, label: item.label });
  });

  router.getRoutes().forEach((record) => {
    const meta = record.meta || {};
    if (!meta.roles || !meta.roles.includes(role)) return;
    if (seen.has(record.path)) return;
    seen.add(record.path);
    items.push({ path: record.path, label: meta.title || record.path });
  });

  return items;
});

// 点完菜单项自动收起抽屉，否则窄屏下新页面会被侧栏盖住
watch(
  () => route.path,
  () => {
    menuOpen.value = false;
  }
);

/** 顶栏显示中文角色名，而不是 admin/member 这样的原始值 */
const roleLabel = computed(() => auth.currentRoleLabel.value);

/**
 * 各角色菜单的展示顺序与专属叫法；路由表里多出来的页面会自动追加在后面。
 *
 * 两条约定（改菜单时请守住）：
 * 1. 只列本角色的职责页面——前台工作台不给管理员、教练管理不给前台。
 *    这里写错了也没关系，navItems 会用路由表的 meta.roles 再过滤一遍。
 * 2. 不要放 /agent：AI 助手的入口是右下角悬浮球，全局常驻，不需要菜单项。
 */
const NAV_ORDER = {
  admin: [
    { path: "/dashboard", label: "数据大盘" },
    { path: "/members", label: "会员管理" },
    { path: "/coaches", label: "教练管理" },
    { path: "/staff", label: "运营人员" },
    { path: "/courses", label: "课程与预约" },
    { path: "/equipment", label: "器材管理" },
    { path: "/system", label: "系统配置" },
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
    { path: "/courses", label: "课程" },
    { path: "/appointments", label: "我的预约" }
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
    "/courses": "预约课程",
    "/appointments": "我的预约"
  }
};

const topbarTitle = computed(() => {
  const titles = ROLE_PAGE_TITLES[useStore.role];
  if (titles && titles[route.path]) {
    return titles[route.path];
  }
  return route.meta.title;
});

/**
 * 退出登录。
 * 后端没有 logout 接口，属纯前端清理：清空 store 与 localStorage 里的 token，
 * 再回到登录页并给出一条提示，避免残留上一次的身份信息。
 *
 * ⚠️ 这里**必须**销毁 AI 助手客户端：它是单例，令牌和会话都在创建时固定下来，
 * 而退出登录只是路由跳转、不刷新页面。不销毁的话，换个账号登进来，
 * 聊天窗里还是上一个人的身份和对话记录。
 */
function handleLogout() {
  destroyAgent();
  auth.logout();
  sessionStorage.setItem("gym_login_notice", "已安全退出登录");
  router.replace("/login");
}
</script>
