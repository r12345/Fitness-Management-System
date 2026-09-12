import request from './request.js'
export function get_dashboard_summary(period){
    return request({
        url: '/dashboard/summary',
        method: 'get',
        params: {
            period: period
        }
    })
}

export function get_dashboard_trend(period){
    return request({
        url: '/dashboard/trend',
        method: 'get',
        params: {
            period:period
        }
    })
}

export function get_card_distribution(){
    return request({
        url: '/dashboard/card-distribution',
        method: 'get',
    })
}


export function get_recent_appointments(){
    return request({
        url: '/dashboard/recent-appointments',
        method: 'get',
    })
}

