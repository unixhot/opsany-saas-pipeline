import request from '@/utils/request'

export const getBusinessTree = (data = {}) => {
    return request({
        url: "business-tree/",
        method: "get",
        params: data
    })
}