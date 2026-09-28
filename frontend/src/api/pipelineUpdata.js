import request from '@/utils/request'

export function pipelineUpdata(data) {
    return request({
        url: "pipeline/",
        method: 'post',
        data
    })
}

export function pipelineBuildUpdata(data) {
    return request({
        url: "pipeline-build/",
        method: 'post',
        data
    })
}