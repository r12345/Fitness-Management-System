import request from './request'
export function getMemberList(data) {
    return request({
        url: '/members/',
        method: 'get',
        params:{
           page:data.page,
           page_size:data.page_size,
           keyword:data.keyword,
            status:data.status,
            card_type:data.card_type,
        }
    })
}
export function addMember(formData) {
    return request({
        url: '/members/',
        method: 'post',
        data: formData
    })
}
export function deleteMember(id) {
    return request({
        url: `/members/${id}`,
        method: 'delete',
    })
}
export function renewMember(id,data) {
    return request({
        url: `/members/${id}/renew`,
        method: 'put',
        data: data
    })
}

export function get_detail(id) {
    return request({
        url: `/members/${id}`,
        method: 'get',
    })
}


export function updateMember(id,formData) {
    return request({
        url: `/members/${id}`,
        method: 'put',
        data: formData
    })
}

export function updateMemberStatus(id,data) {
    return request({
        url: `/members/${id}/status`,
        method: 'put',
        data: data
    })
}