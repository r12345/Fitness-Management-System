import request from "./request";
export function list_courses(data) {
  return request({
      url: "/courses/",
      method: "get",
      params:{
          page: data.page,
          page_size: data.page_size,
          keyword: data.keyword,
          course_type:data.course_type,
          category:data.category,
          status:data.status,
          coach_id:data.coach_id,
      }
  })
}

export function create_courses(data) {
  return request({
      url: "/courses/",
      method: "post",
      data:data
  })
}

export function delete_courses(id) {
  return request({
      url: `/courses/${id}`,
      method: "delete",
  })
}

export function update_courses(id,data) {
  return request({
      url: `/courses/${id}`,
      method: "put",
      data:data
  })
}
export function toggle_courses(id,data) {
  return request({
      url: `/courses/${id}/toggle`,
      method: "post",
      data:data
  })
}

export function get_course_appointments(id) {
  return request({
      url: `/courses/${id}/appointments`,
      method: "get",
  })
}

// 上课地点候选（课程表单的地点输入框 + 教练改排课的地点输入框共用）
// 只有"常用值"，地点仍然可以自由输入
export function list_course_locations() {
  return request({
      url: "/courses/locations",
      method: "get",
  })
}

// 全部教练的排课（会员「预约课程」页的课表来源）
// 会员约的是这里的具体某一次课：带日期、时段、地点与是否可约
export function list_course_schedules(params) {
  return request({
      url: "/courses/schedules",
      method: "get",
      params: {
          course_type: params?.course_type,
          keyword: params?.keyword,
      }
  })
}