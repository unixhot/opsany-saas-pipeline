import request from '@/utils/request'

import config from '@/config/defaultSettings'
const api = config.baseUrl

export function addTool(data) {
    return request({
        url: 'tool/',
        method: 'post',
        data
    })
}

export function editTool(data) {
    return request({
        url: 'tool/',
        method: 'put',
        data
    })
}

export function getTool(data) {
    return request({
        url: 'tool/',
        method: 'get',
        params: data
    })
}

export function delTool(data) {
    return request({
        url: 'tool/',
        method: 'delete',
        data
    })
}

export function refreshState(data) {
    return request({
        url: 'tool/status/',
        method: 'get',
        data
    })
}

//测试jenkins
export function toolJenkinsTest(data) {
    return request({
        url: 'tool/jenkins/test/',
        method: 'post',
        data,
        showDialog: false,
    })
}

//测试git
export function toolGitTest(data) {
    return request({
        url: 'tool/git/test/',
        method: 'post',
        data,
        showDialog: false,
    })
}