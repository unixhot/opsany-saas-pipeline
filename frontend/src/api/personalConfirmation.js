import request from '@/utils/request';
import config from '@/config/defaultSettings'
const api = config.relativeUrl

//  个人确认通过
export function confirmationProceed(data) {
    return request({
        url: api + "jenkins/job/build/proceed/",
        method: "post",
        data
    })
}

//  个人确认不通过
export function confirmationAbort(data) {
    return request({
        url: api + "jenkins/job/build/abort/",
        method: "post",
        data
    })
}
