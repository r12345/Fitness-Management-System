import request from "./request.js";

/**
 * 登录
 * @returns {Promise<{code:number,msg:string,data:object}>} 统一信封结构
 */
export function login(role, username, password) {
  return request({
    url: "/auth/login/",
    method: "post",
    data: {
      role,
      username,
      password
    }
  })
}

/**
 * 注册新账号。
 *
 * 注意：后端 /auth/register 返回的是 { message: "注册成功" }，**没有 code 字段**，
 * 所以不能用 res.code === 0 判断，要用 isRegisterSuccess()。
 *
 * @param {object} payload
 * @param {string} payload.username 账号
 * @param {string} payload.password 密码
 * @param {string} payload.role     角色 admin/reception/coach/member
 * @param {string} payload.name     姓名
 * @param {string} payload.phone    手机号
 */
export function register({ username, password, role, name, phone }) {
  return request({
    url: "/auth/register",
    method: "post",
    data: {
      username,
      password,
      role,
      name,
      phone,
      // sys_user.status，库中现有账号统一取「正常」
      status: "正常"
    }
  })
}

/** 注册是否成功：兼容后端只返回 message 的写法 */
export function isRegisterSuccess(res) {
  if (!res) return false;
  if (typeof res.code !== "undefined") return res.code === 0;
  return res.message === "注册成功";
}

/**
 * 修改自己的登录密码（四个角色通用）。
 *
 * 只提交当前密码与新密码：改的是「当前登录的这个账号」，
 * 请求体里没有用户名，也就没有「改别人密码」的口子。
 */
export function changePassword(old_password, new_password) {
  return request({
    url: "/auth/password",
    method: "put",
    data: { old_password, new_password }
  })
}

/**
 * 从响应中取出提示文案。
 * 统一信封用 msg，登录失败、注册等旧接口用 message。
 */
export function pickMessage(res, fallback = "操作失败") {
  if (!res) return fallback;
  return res.msg || res.message || fallback;
}
