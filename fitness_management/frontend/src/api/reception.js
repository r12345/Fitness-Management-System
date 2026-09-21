import request from "./request.js";

export function get_summary(){
    return request({
        url: '/reception/summary',
        method: 'get'
    })
}


export function get_recent_business_log(){
    return request({
        url: '/reception/business-log',
        method: 'get'
    })
}

// ===== 运营（前台）人员管理：账号由超级管理员统一开 =====

// 运营人员列表
export function getStaffList() {
    return request({
        url: '/reception/staff',
        method: 'get'
    })
}

// 新增运营人员：后端会同时开一个登录账号（账号=手机号，初始密码 123456）
export function createStaff(data) {
    return request({
        url: '/reception/staff',
        method: 'post',
        data
    })
}

// 删除运营人员：其登录账号一并删除
export function deleteStaff(id) {
    return request({
        url: `/reception/staff/${id}`,
        method: 'delete'
    })
}

// 删除「还没建档案」的运营账号：列表里未建档那类行用它，
// 走的是另一个路由，避免和上面的档案编号混在一套 ID 空间里
export function deleteStaffAccount(userId) {
    return request({
        url: `/reception/staff/account/${userId}`,
        method: 'delete'
    })
}
