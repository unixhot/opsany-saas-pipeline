<template>
    <!-- implementationDetails 构建详情-->
    <div class="main">
        <a-drawer :destroyOnClose="true" width="900" placement="right" :closable="false" :visible="detailsVisible" @close="onClose" :bodyStyle="{ padding: 0 }">
            <div slot="title">
                <p style="font-size: 20px; margin: 0">
                    <a-icon type="arrow-left" @click="onClose" style="margin: 0 20px 0 0; color: #333; cursor: pointer" /><span>查看执行日志 #{{ number }}</span>
                </p>
            </div>
            <a-spin :spinning="spinning">
                <div class="main-content" id="main-content">
                    <pre v-html="detailsData.build_console_output"></pre>
                    <img v-if="detailsData.build_info && detailsData.build_info.building" src="@/assets/spining.gif" alt="" />
                    <a-back-top :visibilityHeight="0" :target="target"> </a-back-top>
                </div>
            </a-spin>
        </a-drawer>
    </div>
</template>

<script>
import { constructionDetails } from '@/api/assemblyLine.js'
import { confirmationProceed, confirmationAbort } from '@/api/personalConfirmation.js'
export default {
    data() {
        return {
            // 构建数据
            detailsData: {},
            // 是否停止循环请求
            destroy: false,
            // 是否展示人工确认
            showConfirm: false,
            // 人工确认内容
            confirmContent: '',
            detailsVisible: false,
            spinning: true,
            job_name: '',
            number: '',
            view_name: '',
        }
    },
    watch: {
        showConfirm(val, oldval) {
            if (val) {
                let _this = this
                this.$confirm({
                    content: _this.confirmContent,
                    onOk() {
                        confirmationProceed({ job_name: _this.job_name, num: _this.number - 0, view_name: _this.view_name }).then((res) => {
                            if (res.code == 200) {
                                // console.log(111)
                            }
                        })
                    },
                    onCancel() {
                        confirmationAbort({ job_name: _this.job_name, num: _this.number - 0, view_name: _this.view_name })
                    },
                    cancelText: '终止',
                })
            }
        },
        'detailsData.build_console_output': {
            handler(val) {
                const activePre = document.getElementById('main-content')
                this.$nextTick(() => {
                    activePre.scrollTop = activePre.scrollHeight
                })
            },
        },
    },

    beforeDestroy() {
        clearInterval(this.time)
        this.destroy = true
    },
    methods: {
        target() {
            return document.getElementById('main-content')
        },
        show(job_name, number, view_name) {
            this.job_name = job_name
            this.number = number
            this.view_name = view_name
            this.detailsVisible = true
            this.destroy = false
            this.getConstructionDetailsData(job_name, number, view_name)
        },
        onClose() {
            this.detailsVisible = false
            this.detailsData = {}
            clearInterval(this.time)
            this.destroy = true
        },
        // 获取详情
        getConstructionDetailsData(job_name, number, view_name) {
            this.spinning = true
            constructionDetails({ job_name: job_name, number: number, view_name: view_name })
                .then((res) => {
                    if (
                        res.code != 502 &&
                        !this.destroy &&
                        res.data &&
                        res.data.build_info &&
                        res.data.build_info.building == true
                    ) {
                        let _this = this
                        this.time = setTimeout(function () {
                            _this.getConstructionDetailsData(job_name, number)
                        }, 3000)
                    }
                    if (res.code == 200 && res.data) {
                        this.detailsData = res.data
                        let pat = /Proceed or Abort[\n]$/
                        // console.log(res.data.build_console_output.match(pat))

                        if (res.data.build_console_output?.match(pat)) {
                            let endIndex = res.data.build_console_output.match(pat).index
                            let starIndex = res.data.build_console_output.lastIndexOf('[Pipeline] input')
                            // console.log(res.data.build_console_output.slice(starIndex+17, endIndex))
                            this.confirmContent = res.data.build_console_output.slice(starIndex + 17, endIndex)
                            // this.showConfirm = true
                        } else {
                            // this.showConfirm = false
                        }
                    }
                })
                .finally(() => {
                    this.spinning = false
                })
        },
    },
}
</script>

<style scoped lang="less">
header {
	border-bottom: 1px solid #ccc;
	padding: 20px;
}
.main-content {
	height: calc(100vh - 55px);
	overflow: scroll;
	// background: #1e1e1e;
    background: #202d40;
	pre {
		overflow-y: auto;
		overflow-x: clip;
		white-space: pre-line;
		word-wrap: break-word;
		white-space: break-spaces;
		width: 100%;
		margin: 0;
		// background: #1e1e1e;
        background: #202d40;
		color: #ccc;
		padding: 10px;
		min-height: 500px;
		/deep/option {
			white-space: break-spaces;
		}
	}
}
</style>
