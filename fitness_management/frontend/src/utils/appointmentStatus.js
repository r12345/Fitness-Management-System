/**
 * 预约状态工具。
 *
 * 库里 `appointment.status` 同时存在「待预约」和「已预约」两种写法：
 * 早期导入的那批数据是「待预约」，而新建预约写的是「已预约」。
 * 两者语义完全一样（都还没签到、都占用课程名额），
 * 所以前端凡是判断「能不能签到 / 能不能取消」的地方都必须同时覆盖，
 * 否则历史数据那一批的行内操作按钮一个都不会出现。
 *
 * 后端对应 fitness_management/utils/status.py，两边口径要一起改。
 */
export const PENDING_STATUSES = ["已预约", "待预约"];

/** 是否为「未签到」的预约状态 */
export function isPendingStatus(status) {
  return PENDING_STATUSES.includes(status);
}

/** 状态 → 徽章样式 */
export function statusClass(status) {
  if (status === "已预约" || status === "待预约") return "info";
  if (status === "已签到" || status === "已完成") return "success";
  if (status === "已取消") return "muted";
  if (status === "冲突") return "danger";
  return "";
}

/**
 * 教练排课状态 → 徽章样式，与教练工作台保持一致：
 * 未开始(黄) / 进行中(蓝) / 已签到(绿) / 已取消(红) / 已结束(灰)。
 * 会员预约视图里同步展示排课状态，两边都用这一套配色。
 */
export function scheduleStatusClass(status) {
  if (status === "未开始") return "warn";
  if (status === "进行中") return "info";
  if (status === "已签到") return "success";
  if (status === "已取消") return "danger";
  if (status === "已结束") return "muted";
  return "";
}
