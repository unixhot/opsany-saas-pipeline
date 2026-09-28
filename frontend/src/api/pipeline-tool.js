import request from '@/utils/request';
import config from '@/config/defaultSettings'
const api = config.relativeUrl

// 获取jenkins命令类型
export const getPipelineTool = (data = {}) => {
    return request({
        url: api+"jenkins/job/pipeline-tool/",
        method: "get",
        params:data
    })
}

// 获取post状态
export const getPipelineToolPost = (data = {}) => {
    return request({
        url: api+"jenkins/job/pipeline-tool-post/",
        method: "get",
        params:data
    })
}