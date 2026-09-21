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
            role:data.role,
            user:data.user,
            start_date:data.start_date,
            end_date:data.end_date,
            page:data.page,
            page_size:data.page_size
        }
    })
}


// 日志筛选下拉的数据源：四个身份（固定）+ 库里实际出现过的操作类型及条数。
// 类型不写死在前端，避免出现「选项和库里存的值对不上、一选就查空」。
export function get_log_meta() {
    return request({
        url: '/system/logs/meta',
        method: 'get'
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

