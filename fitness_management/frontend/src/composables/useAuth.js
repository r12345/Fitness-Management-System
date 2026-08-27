import { computed, ref } from "vue";

const SESSION_KEY = "gym_session";

const ROLE_CONFIG = {
  admin: { name: "超级管理员", home: "/dashboard", avatar: "管" },
  reception: { name: "前台运营", home: "/reception", avatar: "前" },
  coach: { name: "健身教练", home: "/coach", avatar: "教" },
  member: { name: "普通会员", home: "/member", avatar: "会" }
};

const session = ref(readSession());

function readSession() {
  try {
    const value = localStorage.getItem(SESSION_KEY);
    return value ? JSON.parse(value) : null;
  } catch (error) {
    return null;
  }
}

function saveSession(data) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(data));
  session.value = data;
}

function getRoleConfig(role) {
  return ROLE_CONFIG[role] || null;
}

export function useAuth() {
  const isLogin = computed(() => Boolean(session.value));
  const currentRole = computed(() => session.value ? session.value.role : "");
  const currentRoleName = computed(() => session.value ? session.value.roleName : "");
  const currentUser = computed(() => session.value || {});

  function login(role, username) {
    const config = getRoleConfig(role);
    const avatarText = role === "member" || role === "coach"
      ? username.slice(0, 1)
      : config.avatar;
    saveSession({
      role,
      roleName: config.name,
      username,
      avatarText,
      loginAt: new Date().toISOString()
    });
  }

  function logout() {
    localStorage.removeItem(SESSION_KEY);
    session.value = null;
  }

  return {
    session,
    isLogin,
    currentRole,
    currentRoleName,
    currentUser,
    login,
    logout,
    getRoleConfig
  };
}
