import request from "./request";
export function list_my_plans(){
    return request({
        url:'/coach_panel/plans',
        method: 'GET'
    })
}


export function create_training_plan(data){
    return request({
        url:'/coach_panel/plans',
        method: 'post',
        data:{
            member_id:data.member_id,
            goal:data.goal,
            body_part:data.body_part,
            actions:data.actions,
            sets_reps:data.sets_reps,
            frequency:data.frequency,
            start_date:data.start_date,
            end_date:data.end_date,
            remark:data.remark
        }
    })
}

export function update_training_plan(plan_id,data){
    return request({
        url:`/coach_panel/plans/${plan_id}`,
        method: 'put',
        data:{
            member_id:data.member_id,
            goal:data.goal,
            body_part:data.body_part,
            actions:data.actions,
            sets_reps:data.sets_reps,
            frequency:data.frequency,
            start_date:data.start_date,
            end_date:data.end_date,
            remark:data.remark
        }
    })
}