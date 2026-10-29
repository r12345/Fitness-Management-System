/**
 * 预约状态工具。
 *
 * `appointment.status` 里有两种「还没上课」的写法，现在语义不再相同：
 *   · 已预约 —— 正常预约：占用课程名额，到点可签到；
 *   · 待预约 —— 会员在自己已有课的时段又下了一单，前台还没处理冲突，
 *               暂不占名额、也不能签到。「处理冲突」按钮只出现在这种状态上。
 *
 * 「能不能签到 / 能不能取消」不能只看状态 —— 还得看这节课上没上完、签没签过到，
 * 那是后端按排课时间算的口径。所以后端在每一行上下发了 can_checkin / can_cancel，
 * 前端直接用，不要在本地再算一遍（两边迟早对不上，而且失败方式是「点了才报错」）。
 *
 * 后端对应 fitness_management/utils/status.py，两边口径要一起改。
 */
export const BOOKED = "已预约";
export const PENDING = "待预约";
export const CHECKED_IN = "已签到";
export const FINISHED = "已完成";
export const CANCELED = "已取消";
export const CONFLICT = "冲突";

/** 还没签到：会员/前台还能取消 */
export const UNCHECKED_STATUSES = [BOOKED, PENDING];

/** 是否为「时段冲突、等前台处理」的预约 */
export function isConflictPending(status) {
  return status === PENDING;
}

/** 是否还没签到（已预约 / 待预约） */
export function isUnchecked(status) {
  return UNCHECKED_STATUSES.includes(status);
}

/** 这一行能不能签到：后端按上课时段算好下发 */
export function canCheckin(item) {
  return Boolean(item && item.can_checkin);
}

/** 这一行能不能取消：还没签到、且课没上完也没签过到 */
export function canCancel(item) {
  return Boolean(item && item.can_cancel);
}

/** 状态 → 徽章样式 */
export function statusClass(status) {
  if (status === PENDING) return "warn"; // 冲突待处理，需要留意
  if (status === BOOKED) return "info";
  if (status === CHECKED_IN || status === FINISHED) return "success";
  if (status === CANCELED) return "muted";
  if (status === CONFLICT) return "danger";
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

/** 排课已结束/已签到：会员对这条预约什么都不能做 */
export function isScheduleClosed(status) {
  return status === "已结束" || status === "已签到" || status === "已取消";
}
