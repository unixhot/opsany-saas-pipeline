import request from '@/utils/request'

// 获取所有流水线
export function getAllJenkins(data) {
    return request({
        url: 'jenkins/overall-jobs/',
        method: 'get',
        params: data
    })
}

// 获取视图
export function getJenkinsViews(data) {
    return request({
        url: 'jenkins/job/overall-views/',
        method: 'get',
        params: data,
        showDialog: false,
    })
}

// 获取视图
export function addJenkinsViews(data) {
    return request({
        url: 'jenkins/job/overall-views/',
        method: 'post',
        data
    })
}

// 编辑视图
export function editJenkinsViews(data) {
    return request({
        url: 'jenkins/job/overall-views/',
        method: 'put',
        data
    })
}

// 删除视图
export function deleteJenkinsViews(data) {
    return request({
        url: 'jenkins/job/overall-views/',
        method: 'delete',
        data
    })
}


// 获取视图
export function getTemplateConfig(data) {
    return request({
        url: 'jenkins/job/overall-ivew-v2/',
        method: 'get',
        params: data,
        showDialog: false,
    })
}

// 编辑视图开关
export function changeTemplateConfig(data) {
    return request({
        url: 'jenkins/job/overall-ivew-v2/',
        method: 'put',
        data
    })
}


// 获取视图详情(编辑)
export function getOverallView(data) {
    return request({
        url: 'jenkins/job/overall-view/',
        method: 'get',
        params: data
    })
}

