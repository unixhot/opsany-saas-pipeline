<template>
    <div class="main">
        <a-drawer :destroyOnClose="true" width="900" placement="right" :closable="false" :visible="detailsVisible" @close="onClose" :bodyStyle="{ padding: 0 }">
            <div slot="title">
                <p style="font-size: 20px; margin: 0">
                    <a-icon type="arrow-left" @click="onClose" style="margin: 0 20px 0 0; color: #333; cursor: pointer" /><span>{{chName(active)}}-日志</span>
                </p>
            </div>
            <a-spin :spinning="spinning">
                <div class="main-content" id="main-content">
                    <pre v-html="dataText"></pre>
                    <img v-if="detailsData.build_info && detailsData.build_info.building" src="@/assets/spining.gif" alt="" />
                    <a-back-top :visibilityHeight="0" :target="target"> </a-back-top>
                </div>
            </a-spin>
        </a-drawer>
        <a-modal :visible="confirmVisible" :title="false" @cancel="onCancel" :zIndex="1050" :footer="false" width="360px">
            <p style="margin:20px 0 20px 0;">
                <a-icon type="question-circle" style="color:#faad14;font-size:20px;margin-right:10px;" />
                <span style="color:#333;font-size:18px;">{{confirmText}}</span>
            </p>
            <div>
                <p v-if="permission"></p>
                <p v-else-if="submitter && submitter.length>0">您没有操作权限，请联系【 <span v-for="(item,index) in submitter" :key="item.id">{{item.ch_name || item.username}} <span v-if="index<submitter.length-1">、</span></span> 】其中一人进行人工确认操作。</p>
                <p v-else>没有配置确认者，请联系管理员处理。</p>
            </div>
            <footer v-if="permission" style="margin-top:30px;">
                <a-button :loading="btnLoading" @click="onOk('abort')">终止</a-button>
                <a-button :loading="btnLoading" @click="onOk('proceed')" type="primary" style="margin-left:10px;">确认</a-button>
            </footer>
            <footer v-else style="margin-top:30px;">
                <a-tooltip placement="topLeft" title="没有操作权限">
                    <a-button disabled>终止</a-button>
                </a-tooltip>
                <a-tooltip placement="topLeft" title="没有操作权限">
                    <a-button disabled type="primary" style="margin-left:10px;">确认</a-button>
                </a-tooltip>

            </footer>
        </a-modal>
    </div>
</template>

<script>
import { getJenkinsJobStages, getJenkinsJobStageLogs, jenkinsJobInput } from '@/api/assemblyLine'

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
            dataText: "",

            confirmVisible: false,
            btnLoading: false,
            active: {},
            submitter: [], // 确认者列表
            permission: false, // 是否有操作权限
            activeId: 0,
            confirmText: "",

        }
    },
    created() {
        this.job_code = this.$route.query.job_code // 流水线的唯一标识code
        this.build_code = this.$route.query.build_code // 执行记录的唯一标识code
        this.number = this.$route.query.number // 执行记录的编号number
    },
    methods: {
        onOk(type) {
            let query = this.$route.query
            let params = {
                operation_type: type,
                code: query.appCode,
                job_name: query.job_name,
                num: query.number,
                execution_log: this.active._links?.log?.href,
                user_list: this.submitter.map(item => item.username),
            }
            this.btnLoading = true
            jenkinsJobInput(params).then(res => {
                if (res.code == 200) {
                    this.$message.success(res.message)
                    this.confirmVisible = false
                    // this.$emit("updata", this.active)
                    this.activeId = this.active.id
                }
            }).finally(() => {
                this.btnLoading = false
            })
        },
        target() {
            return document.getElementById('main-content')
        },
        onCancel() {
            this.confirmVisible = false
            this.btnLoading = false
            this.$parent.isStop = true
            this.$parent.selectStep = {}
            this.dataText = ""
            this.onClose()
        },
        show(record, type) {
            this.active = record
            if (record.name != "Wait for interactive input" || record.status != "PAUSED_PENDING_INPUT") {
                this.detailsVisible = true
            }
            // 有stageFlowNodes字段代表这事stage，否则是step
            if (record.stageFlowNodes) {

            } else {
                let params = {
                    execution_log_url: record?._links?.log?.href || record?._links?.self?.href,
                    job_code: this.job_code,
                    build_code: this.build_code,
                    number: this.number,
                }

                //  等待人工确认时才需要此参数，否则数据不同
                if (record.name == "Wait for interactive input" && record.status == "PAUSED_PENDING_INPUT") {
                    params.PAUSED_PENDING_INPUT = record.status
                }
                if (type) {
                    this.spinning = true
                }
                getJenkinsJobStageLogs(params).then(res => {
                    this.spinning = false
                    if (record.name == "Wait for interactive input" || record.name == "等待交互式输入") {
                        if (record.status == "PAUSED_PENDING_INPUT") {
                            // 自动刷新时，为避免在请求接口时关闭了窗口，请求完成后自动弹出的问题
                            if (type || !this.$parent.isStop) {
                                let username = this.$store?.state?.user?.userInfo?.username
                                this.submitter = res.data?.submitter
                                this.dataText = res.data?.jenkins_data
                                if ((this.activeId != record.id) || !this.activeId) {
                                    this.confirmVisible = true
                                    this.confirmText = res.data.jenkins_data
                                }
                                let flag = this.submitter.find(item => {
                                    return username == item.username
                                })
                                if (flag) {
                                    this.permission = true
                                } else {
                                    this.permission = false
                                }
                            }
                        } else {
                            if (res.data.operation_data?.user_username) {
                                this.dataText = (res.data.operation_data?.user_ch_name || res.data.operation_data?.user_username) + "(" + res.data.operation_data?.user_username + ")"
                                if (res.data.operation_data?.describe == "继续执行构建") {
                                    this.dataText += " 确认了该操作"
                                } else if (res.data.operation_data?.describe == "终止执行构建") {
                                    this.dataText += " 终止了该操作"
                                }
                            } else {
                                this.dataText = "系统执行"
                            }
                        }
                    } else {
                        this.dataText = res.data?.jenkins_data?.text
                    }
                })
            }
        },
        onClose() {
            this.detailsVisible = false
            this.detailsData = {}
            this.dataText = ""
            clearInterval(this.time)
            this.destroy = true
            this.$parent.isStop = true
            this.$parent.selectStep = {}
        },
        // 将名称转换为中文
        chName(step) {
            if (step?.name) {

            } else {
                return false
            }
            if (step.name == "Git") {
                return "拉取代码"
            } else if (step.name == "Print Message") {
                return "打印消息"
            } else if (step.name == "Shell Script") {
                return "执行Shell脚本"
            } else if (step.name == "Sleep") {
                return "睡眠"
            } else if (step.name == "Write file to workspace") {
                return "写文件"
            } else if (step.name == "Read file from workspace") {
                return "读文件"
            } else if (step.name == "codingArtifactsGeneric") {
                return "上传到制品库"
            } else if (step.name == "Wait for interactive input") {
                return "人工确认"
            } else if (step.name == "nexusArtifactUploader") {
                return "上传制品"
            } else if (step.name == "等待交互式输入") {
                return "人工确认"
            } else {
                return step.name
            }
        },
    }
}
</script>

<style scoped lang="less">
header {
	border-bottom: 1px solid #ccc;
	padding: 20px;
}
footer {
	display: flex;
	justify-content: flex-end;
}
.main-content {
	height: calc(100vh - 55px);
	overflow: scroll;
	background: #202d40;
	pre {
		overflow-y: auto;
		overflow-x: clip;
		white-space: pre-line;
		word-wrap: break-word;
		white-space: break-spaces;
		width: 100%;
		margin: 0;
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