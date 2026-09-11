// 教练管理接口（接口文档 §9）
// 教练工作台相关接口见 ./coach-panel.js
import request from './request';

//9.1 教练分页列表
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
