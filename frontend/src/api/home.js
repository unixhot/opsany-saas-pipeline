import request from '@/utils/request'

// 环形数据
export const getHomePage = (data = {}) => {
    return request({
        url: "home-page/",
        method: "get",
        params: data,
        showDialog: false,
    })
}

// 最近7天部署任务
export const getHomePageSeven = (data = {}) => {
    return request({
        url: "home-page-seven/",
        method: "get",
        params: data,
        showDialog:false,
    })
}

// 应用使用频率排名
export const getHomePageUsedApp = (data = {}) => {
    return request({
        url: "home-page-used-app/",
        method: "get",
        params: data,
        showDialog:false,
    })
}


