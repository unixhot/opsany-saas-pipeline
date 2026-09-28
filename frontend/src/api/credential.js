import request from '@/utils/request'

import config from '@/config/defaultSettings'
const api = config.relativeUrl
// 获取凭据类型
export function getCredentialsType(data) {
    return request({
        url: api + 'jenkins/credentials-type/',
        method: 'get',
        params: data,
    })
}
// 获取凭据数据
export function getCredentials(data) {
    return request({
        url: api + 'jenkins/credentials/',
        method: 'get',
        params: data,
        showDialog:false,
    })
}

// 获取凭据数据(凭据管理页面table数据用)
export function getTableCredentials(data) {
    return request({
        url: api + 'jenkins/credentials/',
        method: 'get',
        params: data,
        showDialog: false,
    })
}

// 新增凭据
export function addCredentials(data) {
    return request({
        url: api + 'jenkins/credentials/',
        method: 'post',
        data,
    })
}
// 删除凭据
export function deleteCredentials(data) {
    return request({
        url: api + 'jenkins/credentials/',
        method: 'delete',
        data,
    })
}

// 修改凭据
export function editCredentials(data) {
    return request({
        url: api + 'jenkins/credentials/',
        method: 'put',
        data,
    })
}