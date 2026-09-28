import request from '@/utils/request'

import config from '@/config/defaultSettings'
const api = config.relativeUrl + 'jenkins/job/'


// 获取流水线数据
export function getAssemblyLine(data) {
    return request({
        url: config.relativeUrl +"jenkins-job/",
        method: 'get',
        params: data,
        showDialog:false
    })
}
// 新增流水线
export function addAssemblyLine(data) {
    return request({
        url: api,
        method: 'post',
        data
    })
}
// 修改名称
export function editAssemblyLine(data) {
    return request({
        url: api+"rename/",
        method: 'put',
        data
    })
}
// 删除
export function delAssemblyLine(data) {
    return request({
        url: api,
        method: 'delete',
        data
    })
}



// 构建立即执行
export function immediatelyAssemblyLine(data) {
    return request({
        url: api + "build/start/",
        method: "post",
        data
    })
}
// 中止构建
export function stopExecution(data) {
    return request({
        url: api + "build/stop/",
        method: "put",
        data
    })
}
// 删除历史记录
export function deleteHistory(data) {
    return request({
        url: api + "build/delete/",
        method: "delete",
        data
    })
}
// 获取构建详情
export function constructionDetails(data) {
    return request({
        url: api + "build-info/",
        method: "get",
        params: data
    })
}

// 获取一条流水线的名称和描述
export function getBasicInformation(data) {
    return request({
        url: api + "rename/",
        method: "get",
        params: data
    })
}

// 获取流水线数据和操作记录
export function getAllAssemblyLine(data) {
    return request({
        url: config.relativeUrl+'jenkins/all-job/',
        method: 'get',
        params: data,
        showDialog:true
    })
}
// 判断目前是否有流水线正在构建
export function hasBuilding(data) {
    return request({
        url: config.relativeUrl+'jenkins/job/building-queue/',
        method: 'get',
        params: data,
        showDialog: false,
    })
}

// 是否收藏
export function jenkinsTags(data) {
    return request({
        url: config.relativeUrl+'jenkins/job/tags/',
        method: 'put',
        data,
        showDialog:true
    })
}

// 获取流水线执行记录数据
export function getBuildHistory(data) {
    return request({
        url: config.relativeUrl+'jenkins/job/build/',
        method: 'get',
        params: data,
    })
}

// 判断当前流水线是否正在构建
export function isBuildingQueue(data) {
    return request({
        url: config.relativeUrl+'jenkins/job/building-queue-internal/',
        method: 'get',
        params: data,
        showDialog:true
    })
}

// 刷新jenkins状态
// export function refreshJenkins(data) {
//     return request({
//         url: config.relativeUrl+'refresh-application-pipelines/',
//         method: 'post',
//         data,
//         showDialog:true
//     })
// }

// 更新正在执行的流水线
export function syncApplicationPipelines(data) {
    return request({
        url: config.relativeUrl+'sync-pipelines/',
        method: 'post',
        data,
        showDialog:true
    })
}

// 刷新按钮
export function refreshJenkinsJobs(data) {
    return request({
        url: config.relativeUrl+'refresh-jenkins-jobs/',
        method: 'post',
        data,
        showDialog:true
    })
}

// 获取流水线全局视图
export function getPipelineView(data) {
    return request({
        url: config.relativeUrl +"pipeline-overall-view/",
        method: 'get',
        params: data,
    })
}

// 获取流水线分组
export function getPipelineGroup(data) {
    return request({
        url: config.relativeUrl +"get-app-pipeline-group/",
        method: 'get',
        params: data,
    })
}

// 获取构建历史阶段
export function getJenkinsJobStages(data) {
    return request({
        url: config.relativeUrl +"jenkins/job/stages/",
        method: 'get',
        params: data,
    })
}

// 获取构建历史指定阶段日志
export function getJenkinsJobStageLogs(data) {
    return request({
        url: config.relativeUrl +"jenkins/job/stage-logs/",
        method: 'get',
        params: data,
    })
}

// 获取用户(人工确认使用)
export function getUserList(data) {
    return request({
        url: "users/",
        method: "get",
        params: data
    })
}

// 人工确认操作
export function jenkinsJobInput(data) {
    return request({
        url: 'jenkins-job-input/',
        method: 'post',
        data,
    })
}
