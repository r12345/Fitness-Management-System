import { computed } from "vue";
import { useUserStore } from "../stores/user";

/**
 * 角色 → 显示名 / 默认首页 / 头像字。
 *
 * 注意：后端 /auth/login/ 返回的 home 固定是 "/dashboard"，对教练和会员并不合适，
 * 所以落地页由前端按角色决定，不直接使用接口返回值。
 */
export const ROLE_CONFIG = {
  admin: { name: "超级管理员", home: "/dashboard", avatar: "管" },
  reception: { name: "前台运营", home: "/reception", avatar: "前" },
  coach: { name: "健身教练", home: "/coach", avatar: "教" },
  member: { name: "普通会员", home: "/member", avatar: "会" }
};

export function getRoleConfig(role) {
  return ROLE_CONFIG[role] || null;
}

/** 按角色取默认首页；未知角色回落到登录页，避免跳到不存在的路由 */
export function homeOfRole(role) {
  const config = getRoleConfig(role);
  return config ? config.home : "/login";
}

/**
 * 认证状态统一入口。
 *
 * 早期版本这里维护了一份独立的 gym_session，与 Pinia 的 user store 各存一份登录态，
 * 导致退出登录清不干净。现在统一以 user store 为唯一数据源，本模块只做读取与封装。
 */
export function useAuth() {
  const store = useUserStore();

  const isLogin = computed(() => Boolean(store.token));
  const currentRole = computed(() => store.role);
  const currentRoleName = computed(() => store.role_name);
  const currentRoleLabel = computed(() => {
    const config = getRoleConfig(store.role);
    return config ? config.name : (store.role || "");
  });
  const currentUser = computed(() => ({
    role: store.role,
    roleName: store.role_name,
    userId: store.user_id,
    roleId: store.role_id
  }));

  /** 写入登录态（登录接口返回的 data 直接传入） */
  function setSession(data) {
    store.setSession(data);
  }

  /** 退出登录：清空全部登录态 */
  function logout() {
    store.reset();
  }

  return {
    isLogin,
    currentRole,
    currentRoleName,
    currentRoleLabel,
    currentUser,
    setSession,
    logout,
    getRoleConfig
  };
}
