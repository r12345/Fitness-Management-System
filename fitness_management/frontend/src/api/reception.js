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