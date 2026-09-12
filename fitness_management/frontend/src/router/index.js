import { createRouter, createWebHistory } from "vue-router";
import { homeOfRole } from "../composables/useAuth";
import { useUserStore } from "../stores/user";
import AppLayout from "../components/AppLayout.vue";
import LoginView from "../views/LoginView.vue";
import DashboardView from "../views/DashboardView.vue";
import ReceptionView from "../views/ReceptionView.vue";
import MembersView from "../views/MembersView.vue";
import CoachesView from "../views/CoachesView.vue";
import CoursesView from "../views/CoursesView.vue";
import EquipmentView from "../views/EquipmentView.vue";
import SystemView from "../views/SystemView.vue";
import MemberCenterView from "../views/MemberCenterView.vue";
import CoachPanelView from "../views/CoachPanelView.vue";
import AppointmentList from "../views/AppointmentList.vue";

const routes = [
  {
    path: "/login",
    name: "login",
    component: LoginView,
    meta: { public: true, title: "登录" }
  },
  {
    // 与 /login 共用同一个组件，组件内按地址切换登录/注册模式
    path: "/register",
    name: "register",
    component: LoginView,
    meta: { public: true, title: "注册" }
  },
  {
    path: "/",
    component: AppLayout,
    children: [
      {
        path: "dashboard",
        name: "dashboard",
        component: DashboardView,
        meta: { roles: ["admin", "reception"], title: "数据大盘" }
      },
      {
        path: "reception",
        name: "reception",
        component: ReceptionView,
        meta: { roles: ["admin", "reception"], title: "前台运营工作台" }
      },
      {
        path: "members",
        name: "members",
        component: MembersView,
        meta: { roles: ["admin", "reception"], title: "会员管理" }
      },
      {
        path: "coaches",
        name: "coaches",
        component: CoachesView,
        meta: { roles: ["admin"], title: "教练管理" }
      },
      {
        path: "courses",
        name: "courses",
        component: CoursesView,
        meta: { roles: ["admin", "reception", "coach", "member"], title: "课程" }
      },
      {
        path: "equipment",
        name: "equipment",
        component: EquipmentView,
        meta: { roles: ["admin", "reception"], title: "器材管理" }
      },
      {
        path: "system",
        name: "system",
        component: SystemView,
        meta: { roles: ["admin"], title: "系统配置" }
      },
      {
        path: "member",
        name: "member",
        component: MemberCenterView,
        meta: { roles: ["admin", "member"], title: "会员个人中心" }
      },
      {
        path: "coach",
        name: "coach",
        component: CoachPanelView,
        meta: { roles: ["admin", "coach"], title: "教练工作台" }
      },
      {
        path: "appointments",
        name: "appointment",
        component: AppointmentList,
        meta: { roles: ["admin", "coach", "reception"], title: "预约管理" }
      }

    ]
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: "/login"
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 未登录也可访问的页面
const whiteList = ["/login", "/register"];

/** 读取当前登录角色。守卫执行时 Pinia 已就绪；异常时降级为不校验角色，避免整站导航被卡住 */
function currentRole() {
  try {
    return useUserStore().role || "";
  } catch (error) {
    return "";
  }
}

// 全局守卫
router.beforeEach((to) => {
  const token = localStorage.getItem("token");
  const isPublic = whiteList.includes(to.path);
  const role = currentRole();

  // 未登录：只放行登录/注册，其余跳登录页并记住原本要去的位置
  if (!token) {
    return isPublic ? true : { path: "/login", query: { redirect: to.fullPath } };
  }

  // 已登录还去登录/注册页：直接回到本角色的工作台
  if (isPublic) {
    const home = role ? homeOfRole(role) : "";
    // 角色缺失时 homeOfRole 会回落到 /login，此时不再重定向，避免自我循环
    return home && home !== to.path ? home : true;
  }

  // 角色越权：路由声明了 meta.roles 但不含当前角色时，退回本角色首页
  const allow = to.meta ? to.meta.roles : null;
  if (allow && role && !allow.includes(role)) {
    return homeOfRole(role);
  }

  return true;
});

export default router;
