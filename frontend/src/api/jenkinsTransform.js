import request from '@/utils/request';
import config from '@/config/defaultSettings'
const api = config.relativeUrl

// pepiline转json
export const toJson = (data = {}) => {
    return request({
        url: api+"jenkins/job/to-json/",
        method: "post",
        data
    })
}


// 验证pepiline语法
export const checkSyntax = (data = {}) => {
    return request({
        url: api+"jenkins/job/check-syntax/",
        method: "post",
        data
    })
}

// json转pepiline
export const toPepiline = (data = {}) => {
    return request({
        url: api+"jenkins/job/to-jenkinsfile/",
        method: "post",
        data
    })
}