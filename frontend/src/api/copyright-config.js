import request from '@/utils/request'

export const getCopyRight = (data) => {
	return request({
		url: "copyright-config/",
		method: "get",
		params: data
	})
}
