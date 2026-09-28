<template>
    <a-config-provider :locale="locale">
        <div id="app" v-if="isWatermarkEnabled" v-watermark="watermarkOptions">
            <router-view />
            <ReLoginModal />
        </div>
        <div id="app" v-else>
            <router-view />
            <ReLoginModal />
        </div>
    </a-config-provider>
</template>

<script>
import { domTitle, setDocumentTitle } from '@/utils/domUtil'
import ReLoginModal from '@/components/ReLoginModal/index.vue'
import { i18nRender } from '@/locales'
import { mapActions } from 'vuex'
import { getUserInfo } from '@/api/user'

export default {
    components: {
        ReLoginModal,
    },
    data() {
        return {
            isWatermarkEnabled: false,
            watermarkOptions: {
                content: '', // 后端返回的水印文本
                font: '16px Microsoft YaHei',
                rotate: 20,
                zIndex: 1000,
                color: 'rgba(0,0,0,0.08)',
                width: 200,
                height: 200,
            },
        }
    },
    methods: {
        getUserInfo() {
            getUserInfo().then((res) => {
                const enabled = res.data.watermark_enable
                const watermarkText = res.data.watermark_content
                this.isWatermarkEnabled = enabled
                this.watermarkOptions.content = watermarkText
            })
        },
    },
    mounted() {
        this.getUserInfo()
    },
    computed: {
        locale() {
            // 只是为了切换语言时，更新标题
            const { title } = this.$route.meta
            title && setDocumentTitle(`${i18nRender(title)} - ${domTitle}`)

            return this.$i18n.getLocaleMessage(this.$store.getters.lang).antLocale
        },
    },
}
</script>
<style  lang="less">
#app {
    #vue-watermark-directive {
        position: fixed !important;
    }
}
</style>