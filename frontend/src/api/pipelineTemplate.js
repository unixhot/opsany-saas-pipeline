import request from '@/utils/request'

import config from '@/config/defaultSettings'
const api = config.relativeUrl + 'jenkins/job/'

// 获取流水线模板分组
export function getPipelineTemplateGroup(data) {
    return request({
        url: api + 'pipeline-template-group/',
        method: 'get',
        params: data,
        showDialog:false,
    })
}

// 添加流水线模板分组
export function addPipelineTemplateGroup(data) {
    return request({
        url: api + 'pipeline-template-group/',
        method: 'post',
        data,
    })
}
// 删除流水线模板分组
export function deletePipelineTemplateGroup(data) {
    return request({
        url: api + 'pipeline-template-group/',
        method: 'delete',
        data,
    })
}

// 修改流水线模板分组
export function editPipelineTemplateGroup(data) {
    return request({
        url: api + 'pipeline-template-group/',
        method: 'put',
        data,
    })
}

// 复制流水线模板
export function copyTemplate(data) {
    return request({
        url: api + 'pipeline-template/copy/',
        method: 'post',
        data,
    })
}
// 删除流水线模板
export function deleteTemplate(data) {
    return request({
        url: api + 'pipeline-template/',
        method: 'delete',
        data,
    })
}

// 新增流水线模板
export function addTemplate(data) {
    return request({
        url: api + 'pipeline-template/',
        method: 'post',
        data,
    })
}
// 获取流水线模板数据
export function getTemplate(data) {
    return request({
        url: api + 'pipeline-template/',
        method: 'get',
        params: data,
    })
}

// 编辑流水线模板
export function editTemplate(data) {
    return request({
        url: api + 'pipeline-template/',
        method: 'put',
        data,
    })
}