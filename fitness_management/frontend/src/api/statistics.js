import request from "./request.js";
export function getEquipmentStatistics() {
    return request({
        url: `/statistics/equipment`,
        method: 'get'
    })
}

export function getCoachStatistics() {
    return request({
        url: `/statistics/coaches`,
        method: 'get'
    })
}


