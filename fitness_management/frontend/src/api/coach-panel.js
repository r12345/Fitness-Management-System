// 教练工作台接口（接口文档 §19 教练工作台 / §14 训练计划）
// 对应后端 /api/v1/coach-panel/*
import request from "./request";

/**
 * 训练计划表单 → 请求体字段，新增与编辑共用同一套映射，
 * 避免两处字段悄悄写歪。
 * @param {Object} data 表单数据
 */
function planPayload(data) {
  return {
    member_id: data.member_id,
    goal: data.goal,
    body_part: data.body_part,
    actions: data.actions,
    sets_reps: data.sets_reps,
    frequency: data.frequency,
    start_date: data.start_date,
    end_date: data.end_date,
    remark: data.remark
  };
}

// 19.5 训练计划列表
export function list_my_plans() {
  return request({
    url: "/coach-panel/plans",
    method: "get"
  });
}

// 19.6 新增训练计划
export function create_training_plan(data) {
  return request({
    url: "/coach-panel/plans",
    method: "post",
    data: planPayload(data)
  });
}

// 14.3 编辑训练计划
export function update_training_plan(plan_id, data) {
  return request({
    url: `/coach-panel/plans/${plan_id}`,
    method: "put",
    data: planPayload(data)
  });
}


export function get_records() {
  return request({
    url: "/coach-panel/records",
    method: "get"
  });
}
export function get_member() {
  return request({
    url: "/coach-panel/students",
    method: "get"
  });
}

// 19.3c 新增学员下拉框的候选会员
// 选项直接来自数据库里的会员（还没归属教练的 + 已经属于我的），
// 教练不用手打姓名，也就不会再造出「同一个人的两条档案」。
export function get_member_options(params) {
  return request({
    url: "/coach-panel/member-options",
    method: "get",
    params
  });
}

// 19.3b 教练新增学员
// 只提交一个 member_id —— 教练做的是「认领已有会员」，不新建档案：
// 会员档案来自前台开卡或本人注册，两者都已带登录账号。
export function assign_coach_student(member_id) {
  return request({
    url: "/coach-panel/students",
    method: "post",
    data: { member_id }
  });
}


// 19.1 我的排课（只返回「今天前后各 2 周」窗口内的排课）
export function list_schedule(params) {
  return request({
    url: "/coach-panel/schedules",
    method: "get",
    params
  });
}

// 19.1b 当前排课窗口的起止日期（窗口天数只写在后端一处，前端不自己算）
export function get_schedule_window() {
  return request({
    url: "/coach-panel/schedules/window",
    method: "get"
  });
}

// 19.1c 训练计划预设候选值（计划表单输入框的 datalist 数据源）
// 只提供"常用值"，字段本身仍然可以自由输入
export function list_plan_presets() {
  return request({
    url: "/coach-panel/plan-presets",
    method: "get"
  });
}

// 19.2 修改排课：日期、开始时间、结束时间、地点都可改（课程归属不可改）
// 排课由课程时间自动派生，没有"手工新增"这个入口了
export function update_schedule(schedule_id, data) {
  return request({
    url: `/coach-panel/schedules/${schedule_id}`,
    method: "put",
    data
  });
}

// 19.7 修改排课状态（签到确认 / 撤销签到）
export function update_schedule_status(schedule_id, status) {
  return request({
    url: `/coach-panel/schedules/${schedule_id}/status`,
    method: "put",
    data: { status }
  });
}

// 19.8 我的资料（查看）
export function get_my_profile() {
  return request({
    url: "/coach-panel/profile",
    method: "get"
  });
}

// 19.9 我的资料（修改）
// 只提交姓名 / 联系方式 / 专长：薪资、在职状态、课时、评分由管理员与系统维护，
// 后端也不收这几项，前端多传也没用。
export function update_my_profile(data) {
  return request({
    url: "/coach-panel/profile",
    method: "put",
    data: {
      name: data.name,
      phone: data.phone,
      specialties: data.specialties
    }
  });
}
