import axios from 'axios'
import store from '@/store'
import storage from 'store'
import notification from 'ant-design-vue/es/notification'
import message from 'ant-design-vue/es/message'
import { VueAxios } from './axios'
import config from '@/config/defaultSettings'
import qs from 'qs'

axios.defaults.withCredentials = true; //让ajax携带cookie


export const getLoginUrl = () => {
    const href = window.location.href;
    const baseurl = window.API_ROOT.split('/')[0]
    return `${baseurl}/login/?c_url=${encodeURIComponent(href)}`;
}

export const loginOut = () => {
    window.location.href = getLoginUrl();
}

// 本次加载是否成功认证过：有成功响应=会话中途失效(弹窗恢复)；从未成功=刷新即失效(跳登录页)
let hasAuthedOnce = false;
const isProd = process.env.NODE_ENV === "production";

// 创建 axios 实例
const request = axios.create({
    // API 请求的默认前缀
    baseURL: config.baseUrl,
    // timeout: 15000 // 请求超时时间
    headers: {
        Authorization: ""
    }
})

// chinese_traditional
// 异常拦截处理器
const errorHandler = (error) => {
    if (error.response) {
        const statusText = error.response.statusText
        notification.error({
            message: '错误',
            description: statusText
        })
    }
    return Promise.reject(error)
}

// request interceptor
request.interceptors.request.use(config => {
    if (config.method.toLowerCase() == 'get') {
        //get请求 序列化数组参数
        config.paramsSerializer = (params) => {
            return qs.stringify(params, { arrayFormat: 'repeat' })
        }
    }
    return config
}, errorHandler)

// response interceptor
request.interceptors.response.use((response) => {
    const showDialog = response.config.showDialog == undefined?true:response.config.showDialog
    const { code, successcode, errcode, errors, status_code, status_info } = response.data;
    if (code == '200' || status_code == 0) {
        hasAuthedOnce = true;
        return response.data
    } else {
        if (errcode == '40100') {
            if (hasAuthedOnce) {
                // 登录失效：广播事件，由宿主 ReLoginModal 弹窗处理
                window.dispatchEvent(new CustomEvent('opsany-header:auth-failed', { detail: response.data }));
            } else {
                isProd && loginOut();
            }
        } else if(!showDialog){
            // 40401   未检测到Jenkins工具配置，请到系统设置，添加工具集成。
            return Promise.reject(response.data)
        } else {
            message.warning({
                content: response.data.message || response.data.errors || status_info
            })
        }
        return Promise.reject(response.data)
    }
}, errorHandler)
const installer = {
    vm: {},
    install(Vue) {
        Vue.use(VueAxios, request)
    }
}

export default request

export {
    installer as VueAxios,
    request as axios
}