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
          status:data.state,
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