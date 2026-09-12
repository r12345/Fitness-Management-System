import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 登录态存储。
 *
 * token 除了保存在 store 里，还单独写一份到 localStorage：
 * axios 请求拦截器和路由守卫都以 localStorage 为准，避免它们依赖 Pinia 实例。
 * 退出登录时两处都要清掉，否则会残留角色信息，出现「退出后仍显示旧身份」。
 */
export const useUserStore = defineStore('users', () => {
  const token = ref('')
  const role = ref('')
  const role_name = ref('')
  const user_id = ref(null)
  const role_id = ref(null)

  function set_role_id(value) {
    role_id.value = value
  }

  function setToken(value) {
    token.value = value || ''
    if (token.value) {
      localStorage.setItem('token', token.value)
    } else {
      localStorage.removeItem('token')
    }
  }

  function setRole(value) {
    role.value = value || ''
  }

  function setRoleName(value) {
    role_name.value = value || ''
  }

  function setUserId(value) {
    user_id.value = value
  }

  /**
   * 一次性写入登录接口返回的完整信息
   * @param {object} data /auth/login/ 响应中的 data
   */
  function setSession(data = {}) {
    setToken(data.token)
    setRole(data.role)
    setRoleName(data.role_name)
    setUserId(data.user_id)
    set_role_id(data.role_id)
  }

  /**
   * 退出登录：清空全部登录态与本地缓存。
   * 后端未提供 logout 接口，属纯前端清理。
   */
  function reset() {
    token.value = ''
    role.value = ''
    role_name.value = ''
    user_id.value = null
    role_id.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    role,
    role_name,
    user_id,
    role_id,
    set_role_id,
    setToken,
    setRole,
    setRoleName,
    setUserId,
    setSession,
    reset
  }
}, {
  persist: true
}
)
