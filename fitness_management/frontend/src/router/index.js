import { createRouter, createWebHistory } from "vue-router";
import { useAuth } from "../composables/useAuth";
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
// 白名单
const whiteList = ['/login','/register']
// 全局守卫路由
router.beforeEach((to, from) => {
  if (!whiteList.includes(to.path)) {
    if (!localStorage.getItem('token')) {
      return '/login'
    }
  }
})


export default router;
