import request from './request'
export function getMemberList() {
    return request({
        url: '/members/',
        method: 'get'
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
export function renewMember(data) {
    return request({
        url: `/members/${data.id}/renew`,
        method: 'put',
        params: {          // ✅ 用 params，axios 会自动拼到 URL query 上
      member_id: data.id,
      renew: data.renew
    }
    })
}