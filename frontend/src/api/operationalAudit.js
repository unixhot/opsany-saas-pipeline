import request from '@/utils/request';

//获取 操作审计table数据
export const getOperationAudit = (data = {}) => {
    return request({
        url: "get-operation-audit/",
        method: "get",
        params: data
    })
}

//获取 操作审计详情
export const getOperationLog = (data = {}) => {
    return request({
        url: "get-operation-log/",
        method: "get",
        params: data
    })
}