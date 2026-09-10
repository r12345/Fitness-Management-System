import request from "./request.js";
export function getEquipmentStatistics() {
    return request({
        url: `/statistics/equipment`,
        method: 'get'
    })
}

