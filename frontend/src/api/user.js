import request from '@/utils/request';

/**
 * @deprecated  用户信息相关
 * @param {data} Object
 * @returns Promise
 */
//获取用户信息
export const getUserInfo = (data = {}) => {
    return request({
        url: "user_info/",
        method: "get",
        params: data
    })
}


/**
 * @deprecated  上传头像
 * @param {data} Object
 * @returns Promise
 */
//上传图标
export const uploadHeadImg = (data = {}) => {
    return request({
        url: "user-icon/",
        method: "post",
        data
    })
}