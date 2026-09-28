import request from '@/utils/request'

import config from '@/config/defaultSettings'
const api = config.relativeUrl
// 获取流水线配置数据(命令)
export function getReconfig(data) {
    return request({
        url: api + 'jenkins/job/reconfig/script/',
        method: 'get',
        params: data
    })
}

// 提交流水线配置数据(命令)
export function editReconfig(data) {
    return request({
        url: api + 'jenkins/job/reconfig/script/',
        method: 'put',
        data
    })
}

// 获取流水线触发规则
export function getTriggerBuildParams(data) {
    return request({
        url: api + 'jenkins/job/reconfig/triggers/',
        method: 'get',
        params: data
    })
}

// 提交流水线触发规则
export function editTriggerBuildParams(data) {
    return request({
        url: api + 'jenkins/job/reconfig/triggers/',
        method: 'put',
        data
    })
}

// 获取流水线参数设置数据
export function getParameterSetting(data) {
    return request({
        url: api + 'jenkins/job/reconfig/parameter/',
        method: 'get',
        params: data
    })
}

// 提交流水线参数设置数据
export function editParameterSetting(data) {
    return request({
        url: api + 'jenkins/job/reconfig/parameter/',
        method: 'put',
        data
    })
}