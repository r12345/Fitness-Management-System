import request from './request.js'

export function get_member_info(){
  return request({
    url: '/member_center/',
    method: 'get'
  })
}

export function getMyAppointments(){
  return request({
    url: '/member_center/appointments',
    method: 'get'
  })
}

export function getMyCourses(){
  return request({
    url: '/member_center/courses',
    method: 'get'
  })
}

/** 会员本人签到：只在上课时段内放行，签到即按课时费从余额扣款。
    走 /member_center 而不是 /appointments —— 后者是前台/教练/管理员的代签入口。 */
export function checkinMyAppointment(appointmentId){
  return request({
    url: `/member_center/appointments/${appointmentId}/checkin`,
    method: 'post'
  })
}

/** 会员可预约的排课：全部教练、从今天起往后 4 周的排课（含课程/教练/时间/地点/状态） */
export function getUpcomingSchedules(){
  return request({
    url: '/member_center/schedules',
    method: 'get'
  })
}


export function editProfile(data){
  return request({
    url: '/member_center/profile',
    method: 'put',
    data:data
  })
}