import request from './request'

// 预约分页列表
export function list_appointments(params) {
  return request({
    url: '/appointments',
    method: 'get',
    params
  })
}

// 会员预约课程
export function create_appointment(data) {
  return request({
    url: '/appointments',
    method: 'post',
    data:data
  })
}

// 取消预约
export function cancel_appointment(appointment_id) {
  return request({
    url: `/appointments/${appointment_id}`,
    method: 'delete'
  })
}

// 预约签到
export function checkin_appointment(appointment_id) {
  return request({
    url: `/appointments/${appointment_id}/checkin`,
    method: 'post'
  })
}

// 冲突处理
export function resolve_appointment(appointment_id, data) {
  return request({
    url: `/appointments/${appointment_id}/resolve`,
    method: 'put',
    data
  })
}