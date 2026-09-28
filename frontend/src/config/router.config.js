// eslint-disable-next-line
import { UserLayout, BasicLayout, BlankLayout, PageView } from '@/layouts'
const RouteView = {
	name: 'RouteView',
	render: (h) => h('router-view')
}

/**
 * 菜单级别路由
 * @type { *[] }
 */
export const asyncRouterMap = [{
	path: '/',
	name: 'index',
	component: BasicLayout,
	meta: { title: 'menu.home' },
	redirect: '/home',
	children: [{
		path: '/home',
		name: 'home',
		component: () => import('@/views/home'),
		meta: { title: '概览', keepAlive: false, icon: "home" }
	},]
},

]

/**
 * 基础路由
 * @type { *[] }
 */
export const constantRouterMap = [{
	path: '/404',
	component: () => import( /* webpackChunkName: "fail" */ '@/views/exception/404')
},
{
	path: '/403',
	component: () => import('@/views/exception/403')
}, {
	path: '/error',
	component: () => import('@/views/exception/error')
}
]


/**
 * 不在菜单栏的路由 例：详情页路由
 * @type { *[] }
 */
export const detailRouterMap = [
	{
		path: '/applicationDelivery/assemblyLine/pipelineConfiguration',
		name: 'pipelineConfiguration',
		component: () => import('@/views/applicationDelivery/pipelineConfiguration.vue'),
		hidden: true,
		meta: {
			title: '流水线配置',
			parentRouteName: 'assemblyLine'
		},
	},
    {
        name:"setPipelineTemplate",
        path:"/setting/pipelineTemplate/setPipelineTemplate",
        component:()=>import("@/views/setting/setPipelineTemplate/pipelineConfiguration.vue"),
        hidden:true,
        meta: { title: '模板设置', keepAlive: false }
    },
    {
        name:"executionLog",
        path:"/applicationDelivery/assemblyLine/executionLog",
        component:()=>import("@/views/applicationDelivery/executionLog.vue"),
        hidden:true,
        meta: { title: '流水线执行历史', keepAlive: false }
    },
    {
        name:"executionLogDefault",
        path:"/applicationDelivery/assemblyLine/executionLogDefault",
        component:()=>import("@/views/applicationDelivery/executionLogDefault.vue"),
        hidden:true,
        meta: { title: '执行详情', keepAlive: false }
    },
]