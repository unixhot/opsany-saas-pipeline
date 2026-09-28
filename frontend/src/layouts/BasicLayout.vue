<template>
    <div>
        <pro-layout
            :title="title"
            :logo="require('../assets/logo-reverse.png')"
            :menus="menus"
            :collapsed="collapsed"
            :mediaQuery="query"
            :isMobile="isMobile"
            :handleMediaQuery="handleMediaQuery"
            :handleCollapse="handleCollapse"
            :i18nRender="i18nRender"
            v-bind="settings"
            style="padding: 20px"
            :menuHeaderRender="menuHeaderRender"
            ref="proLayout1"
        >
            <!-- <setting-drawer :settings="settings" @change="handleSettingChange" /> -->
            <template v-slot:rightContentRender>
                <!-- 公共 header：导航/控制台/工作台/消息/支持/用户菜单整体替换为 <opsany-header>（UMD 由 index.html 加载） -->
                <opsany-header platform="pipeline"></opsany-header>
            </template>
            <template v-slot:footerRender>
                <global-footer />
            </template>
            <router-view />
			<opsany-chat-modal v-if="!isDev && $store.state.user.userInfo.ai_assistant"></opsany-chat-modal>
        </pro-layout>
    </div>
</template>


<script>
import { SettingDrawer } from '@ant-design-vue/pro-layout'
import { i18nRender } from '@/locales'
import { mapState, mapActions } from 'vuex'
import { SIDEBAR_TYPE, TOGGLE_MOBILE_TYPE } from '@/store/mutation-types'
import { asyncRouterMap } from '@/config/router.config.js'

import defaultSettings from '@/config/defaultSettings'
import GlobalFooter from '@/components/GlobalFooter'
import opsLogo from '../assets/ops-logo.png'
import storage from 'store'
import { updateTheme } from '@/utils/util'
export default {
    name: 'BasicLayout',
    components: {
        SettingDrawer,
        GlobalFooter,
    },
    data() {
        return {
            // preview.pro.antdv.com only use.
            isProPreviewSite: process.env.VUE_APP_PREVIEW === 'true' && process.env.NODE_ENV !== 'development',
            // end

            // base
            menus: [],
            // 侧栏收起状态
            collapsed: false,
            title: defaultSettings.title,
            settings: {
                // 布局类型
                layout: defaultSettings.layout, // 'sidemenu', 'topmenu'
                // 定宽: true / 流式: false
                contentWidth: defaultSettings.layout === 'sidemenu' ? false : defaultSettings.contentWidth === 'Fixed',
                // 主题 'dark' | 'light'
                theme: defaultSettings.navTheme,
                // 主色调
                primaryColor: defaultSettings.primaryColor,
                fixedHeader: defaultSettings.fixedHeader,
                fixSiderbar: defaultSettings.fixSiderbar,
                colorWeak: defaultSettings.colorWeak,

                hideHintAlert: false,
                hideCopyButton: false,
            },
            // 媒体查询
            query: {},

            // 是否手机模式
            isMobile: false,

            menuHeaderRender: (title, logo) => {
                return (
                    <a href="#" onClick={this.clickLogo}>
                        {logo}
                        <h1>{defaultSettings.title}</h1>
                    </a>
                )
            },
        }
    },
    computed: {
        ...mapState({
            // 动态主路由
            mainMenu: (state) => state.permission.addRouters,
        }),
		isDev() {
			return process.env.NODE_ENV === "development";
		},
    },
    created() {
        // this.menus = asyncRouterMap.find((item) => item.path === '/').children
        this.menus = this.mainMenu.find((item) => item.path === '/').children
        this.collapsed = !this.sidebarOpened
        // 公共 header 接口固定走 workbench 后端（全局账号体系）。
        // dev 下注入 workbench dev 后端地址；prod 无需注入（header 自动推导 /{根}/workbench/api/workbench/v0_1/）
        if (process.env.NODE_ENV === "development") {
            window.OPSANY_HEADER_API_BASE = "http://192.168.0.7:8004/api/workbench/v0_1/";
        }
    },
    mounted() {
        const { $nextTick: nextTick } = this
        this.getUserInfo()
        const userAgent = navigator.userAgent
        if (userAgent.indexOf('Edge') > -1) {
            this.$nextTick(() => {
                this.collapsed = !this.collapsed
                setTimeout(() => {
                    this.collapsed = !this.collapsed
                }, 16)
            })
        }
        // first update color
        const themeName = storage.get('opsany-theme')
        themeName && updateTheme(themeName)
        !themeName && updateTheme('theme-default')
    },
    methods: {
        ...mapActions(['getUserInfo']),
        i18nRender,
        handleMediaQuery(val) {
            this.query = val
            if (this.isMobile && !val['screen-xs']) {
                this.isMobile = false
                return
            }
            if (!this.isMobile && val['screen-xs']) {
                this.isMobile = true
                this.collapsed = false
                this.settings.contentWidth = false
                // this.settings.fixSiderbar = false
            }
        },
        handleCollapse(val) {
            this.collapsed = val
        },
        handleSettingChange({ type, value }) {
            type && (this.settings[type] = value)
            switch (type) {
                case 'contentWidth':
                    this.settings[type] = value === 'Fixed'
                    break
                case 'layout':
                    if (value === 'sidemenu') {
                        this.settings.contentWidth = false
                    } else {
                        this.settings.fixSiderbar = false
                        this.settings.contentWidth = true
                    }
                    break
            }
        },
        clickLogo(e) {
            window.location.href = window.API_ROOT
        },
        logoRender() {
            return <image src={opsLogo} />
        },
    },
}
</script>

<style lang="less">
@import './BasicLayout.less';
#logo {
    a {
        img {
            width: 32px;
            height: 32px;
        }
    }
}
</style>
