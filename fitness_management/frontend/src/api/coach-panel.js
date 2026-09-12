// 教练工作台接口（接口文档 §19 教练工作台 / §14 训练计划）
// 对应后端 /api/v1/coach_panel/*（后端同时兼容中划线 /api/v1/coach-panel/*）
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
    url: "/coach_panel/plans",
    method: "get"
  });
}

// 19.6 新增训练计划
export function create_training_plan(data) {
  return request({
    url: "/coach_panel/plans",
    method: "post",
    data: planPayload(data)
  });
}

// 14.3 编辑训练计划
export function update_training_plan(plan_id, data) {
  return request({
    url: `/coach_panel/plans/${plan_id}`,
    method: "put",
    data: planPayload(data)
  });
}


export function get_records() {
  return request({
    url: "/coach_panel/records",
    method: "get"
  });
}
export function get_member() {
  return request({
    url: "/coach_panel/students",
    method: "get"
  });
}


// 19.2 新增排课
export function addSchedule(data) {
  return request({
    url: "/coach_panel/schedules",
    method: "post",
    data
  });
}
