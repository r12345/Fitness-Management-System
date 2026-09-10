import request from './request.js'
export function list_schedule() {
    return request({
        url: '/schedule/schedules',
        method: 'get'
    })
}

export function create_schedule(data) {
    return request({
        url: '/schedule/schedules',
        method: 'post',
        data:data
    })
}

