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


export function editProfile(data){
  return request({
    url: '/member_center/profile',
    method: 'put',
    data:data
  })
}