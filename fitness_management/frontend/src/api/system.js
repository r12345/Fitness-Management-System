import request from './request.js'

export function getSystemConfig() {
    return request({
        url: '/system/config',
        method: 'get'
    })
}


export function updateSystemConfig(data) {
    return request({
        url: '/system/config',
        method: 'put',
        data:{
            gym_name:data.gym_name,
            address:data.address,
            business_hours:data.business_hours,
            phone:data.phone
        }
    })
}


export function list_system_logs(data) {
    return request({
        url: '/system/logs',
        method: 'get',
        params:{
            log_type:data.log_type,
            user:data.user,
            start_date:data.start_date,
            end_date:data.end_date,
            page:data.page,
            page_size:data.page_size
        }
    })
}


export function list_dicts() {
    return request({
        url: '/system/dicts',
        method: 'get'
    })
}

export function create_dicts(data) {
    return request({
        url: '/system/dicts',
        method: 'post',
        data:{
            dict_type:data.dict_type,
            dict_value:data.dict_value,
            status:data.status,
        }
    })
}

