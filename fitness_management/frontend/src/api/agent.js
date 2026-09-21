import request from "./request";

/**
 * 取当前登录用户专属的扣子（Coze）访问令牌，用于实现会话隔离。
 *
 * 后端用 OAuth 应用私钥签 JWT（payload 里带 session_name = 业务侧用户 ID），
 * 再换成 access_token 返回。私钥不下发到浏览器。
 *
 * 返回 data 的两种形态：
 *   启用隔离：{ enabled: true, token, expires_in, session_name, bot_id }
 *   未配置时：{ enabled: false, reason, bot_id }   → 调用方应回退到公共令牌
 */
export function get_agent_token() {
  return request({
    url: "/agent/token",
    method: "get"
  });
}
