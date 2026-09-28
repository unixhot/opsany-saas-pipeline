import request from '@/utils/request'

import config from '@/config/defaultSettings'
const api = config.relativeUrl

// 获取gitlab项目
export function getProjects(data) {
    return request({
        url: api + 'gitlab/projects/',
        method: 'get',
        params: data,
        showDialog:false,
    })
}

// 获取分支
export function getBranch(data) {
    return request({
        url: api + 'gitlab/project/branch/',
        method: 'get',
        params: data,
    })
}
