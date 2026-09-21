import { createRouter, createWebHistory } from "vue-router";
import { homeOfRole } from "../composables/useAuth";
import { useUserStore } from "../stores/user";
import AppLayout from "../components/AppLayout.vue";
import LoginView from "../views/LoginView.vue";
import DashboardView from "../views/DashboardView.vue";
import ReceptionView from "../views/ReceptionView.vue";
import MembersView from "../views/MembersView.vue";
import CoachesView from "../views/CoachesView.vue";
import StaffView from "../views/StaffView.vue";
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
        // 前台工作台只给前台：超级管理员是管全局的，接待台不是他的职责。
        // 原来这里是 ["admin","reception"]，管理员的侧栏里就多出一个「前台运营工作台」。
        meta: { roles: ["reception"], title: "前台运营工作台" }
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
        path: "staff",
        name: "staff",
        component: StaffView,
        // 运营（前台）人员的账号由超级管理员统一开，前台自己不需要这一页
        meta: { roles: ["admin"], title: "运营人员" }
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
        // 会员中心接口按当前登录用户查会员档案，非会员角色没有档案，会 404
        meta: { roles: ["member"], title: "会员个人中心" }
      },
      {
        path: "coach",
        name: "coach",
        component: CoachPanelView,
        // 后端 get_current_coach 只放行 role=coach，其他角色一律 403
        meta: { roles: ["coach"], title: "教练工作台" }
      },
      {
        path: "appointments",
        name: "appointment",
        component: AppointmentList,
        // 后端 /appointments 对会员只返回本人记录、取消时也校验归属，
        // 所以会员可以进这一页（页面里本来就有「我的预约」分支，之前路由却被挡住了）
        meta: { roles: ["admin", "coach", "reception", "member"], title: "预约管理" }
      }
      // 原本这里还有 /agent「AI 助手」页面：不承载业务，且和全局悬浮球（AgentFab）
      // 是重复入口，已连页面文件一起删除。AI 助手现在只有一个入口 —— 悬浮球。

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

  // "/" 只是承载布局的父路由，自身没有页面内容。
  // 走到这里说明回跳目标落回了根路径（例如登录页带的 redirect=/），
  // 必须按角色送回各自首页，否则会停在「有侧栏、主区域全空」的空白页。
  if (to.path === "/") {
    const home = homeOfRole(role);
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
