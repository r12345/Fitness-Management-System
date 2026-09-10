import request from './request.js'
export function getEquipmentList(queryData) {
  return request({
    url: '/equipment',
    method: 'get',
    params :{
        keyword:queryData.keyword,
        category:queryData.category,
        status:queryData.status,
        page:queryData.page,
        page_size:queryData.page_size
    }
  })
}

export function create_equipment(formData) {
  return request({
    url: '/equipment',
    method: 'post',
    data :{
        name:formData.name,
        model:formData.model,
        category:formData.category,
        location:formData.location,
        purchase_date:formData.purchase_date,
        price:formData.price,
        status:formData.status,
        remark:formData.remark
    }
  })
}

export function update_equipment(id,formData) {
  return request({
    url: `/equipment/${id}`,
    method: 'patch',
    data :{
        name:formData.name,
        model:formData.model,
        category:formData.category,
        location:formData.location,
        purchase_date:formData.purchase_date,
        price:formData.price,
        status:formData.status,
        remark:formData.remark
    }
  })
}


export function delete_equipment(id) {
  return request({
    url: `/equipment/${id}`,
    method: 'delete',
  })
}

export function create_repair(id,formData) {
  return request({
    url: `/equipment/${id}/repair`,
    method: 'post',
    data:{
       description:formData.description,
        cost:formData.cost,
        repair_time:formData.repair_time,
       remark:formData.remark
    }
  })
}

export function create_maintenance(id,formData) {
  return request({
    url: `/equipment/${id}/maintenance`,
    method: 'post',
      data:{
        maintenance_time:formData.maintenance_time,
         person:formData.person,
        content:formData.content
      }
  })
}