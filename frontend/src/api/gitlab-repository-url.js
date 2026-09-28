
import request from '@/utils/request'

import config from '@/config/defaultSettings'
const api = config.relativeUrl

// 获取代码仓库数据
export function getRepository(data) {
    return request({
        url: 'gitlab-repository-url/',
        method: 'get',
        params: data,
        showDialog:false,
    })
}
