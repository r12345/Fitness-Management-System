import request from './request.js'
export function create_checkin(checkin_time){
    return request({
        url: '/training/checkin',
        method: 'post',
        data:{
            checkin_time:checkin_time
        }
    })
}

export function leave_checkin(checkin_id,leave_time){
    return request({
        url: `/training/checkin/${checkin_id}/leave`,
        method: 'put',
        data:{
            leave_time:leave_time
        }
    })
}

export function list_my_checkins(){
    return request({
        url: `/training/checkin`,
        method: 'get',
    })
}

export function create_training_records(data){
    return request({
        url: `/training/records`,
        method: 'post',
        data:{
            member_id:data.member_id,
            train_date:data.train_date,
            content:data.content,
            weight:data.weight,
            duration_minutes:data.duration_minutes,
            fat_rate:data.fat_rate,
            body_weight:data.body_weight,
        }
    })
}

export function list_training_records(){
    return request({
        url: `/training/records`,
        method: 'get',
    })
}

export function get_training_statistics(period){
    return request({
        url: `/training/statistics`,
        method: 'get',
        params:{
            period:period
        }
    })
}
