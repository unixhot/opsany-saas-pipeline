import request from '@/utils/request'

/**
 * @descript  获取菜单列表
 * @param {data} Object
 * @returns Promise
 */

export const getMenuList = (data = {}) => {
    return request({
        url: "get-menu/",
        method: "get",
        params: data
    })
}
