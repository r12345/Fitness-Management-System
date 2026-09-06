import request from './request';
export function getCoachList(data) {
    return request({
        url: '/coaches/',
        method: 'get',
        params:{
            keyword:data.keyword,
            status:data.status,
            specialty:data.specialty,
            page:data.page,
            page_size:data.page_size

        }
    })
}

//9.2 新增教练
export function addCoach(data){
  return request({
    url:'/coaches',
    method:'post',
    data
  })
}

//9.3编辑教练
export function updateCoach(id,data){
  return request({
    url:`/coaches/${id}`,
    method:'put',
    data:data
  })
}

//9.4删除教练
export function deleteCoach(id){
  return request({
    url:`/coaches/${id}`,
    method:'delete'
  })
}

//9.5教练授课统计
export function getCoachStat(coachId){
  return request({
    url:`/coaches/${coachId}/statistics`,
    method:'get'
  })
}

// 教练工作台：获取我的排课
export function getSchedules() {
  return request({
    url: '/coach_panel/schedules',
    method: 'get'
  })
}

// 教练工作台：新增排课
export function addSchedule(data) {
  return request({
    url: '/coach_panel/schedules',
    method: 'post',
    data
  })
}