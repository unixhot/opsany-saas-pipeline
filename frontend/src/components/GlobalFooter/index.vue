<template>
    <global-footer class="footer custom-render" v-if="showFooter">
        <template v-slot:links></template>
        <template v-slot:copyright>
            <div v-html="content"></div>
        </template>
    </global-footer>
</template>

<script>
import { GlobalFooter } from '@ant-design-vue/pro-layout'
import { getCopyRight } from '@/api/copyright-config'
import { mapMutations, mapState } from "vuex";
export default {
    name: 'ProGlobalFooter',
    components: {
        GlobalFooter,
    },
    data() {
        return {
            content: undefined,
        }
    },
    methods: {
        getCopyRight() {
            getCopyRight().then((res) => {
                this.content = res.data.content
            })
        },
    },
    mounted() {
        this.getCopyRight()
    },
	computed: {
		...mapState({
			showFooter: state => state.user.userInfo?.copyright_config,
		}),
	},
}
</script>
<style scoped lang="less">
.footer {
    /deep/ .ant-pro-global-footer-copyright {
        p {
            margin-bottom: 5px;
        }
    }
}
</style>