<template>
    <!-- triggerRule 触发规则 -->
    <div class="triggerRule_main">
        <a-spin :spinning="spinloading">
            <div class="block">
                <a-collapse activeKey="1">
                    <template #expandIcon="props">
                        <a-icon type="caret-right" :rotate="props.isActive ? 90 : 0" />
                    </template>
                    <a-collapse-panel key="1" :header="language.trigger_header1">
                        <div style="margin: 0 0 0 26px">
                            <h4 style="margin: 0">
                                {{ language.trigger_message1 }}：
                                <a-switch
                                    @change="onChange"
                                    v-model="isTrigger"
                                    style="margin: 0 10px 0 0"
                                ></a-switch>
                            </h4>
                            <div v-if="isTrigger">
                                <a-spin :spinning="spinning1">
                                <p style="font-size: 12px; color: #888; margin: 0 0 20px 0">
                                    {{ language.trigger_message3 }}
                                </p>
                                <div>
                                    <span>{{ language.trigger_message4 }}：</span>
                                    <a-select
                                        v-if="!gitError"
                                        @change="projectsChange"
                                        v-model="project_id"
                                        :placeholder="language.trigger_placeholder1"
                                        style="width: 400px; margin: 0 0 20px 0"
                                        optionFilterProp="label"
                                        showSearch
                                    >
                                        <a-select-option
                                            :title="item.ssh_url_to_repo"
                                            v-for="item in projectsList"
                                            :key="item.id"
                                            :value="item.id"
                                            :label="item.ssh_url_to_repo"
                                        >
                                            {{ item.ssh_url_to_repo }}
                                        </a-select-option>
                                    </a-select>
                                    <a-tooltip v-else>
                                        <template slot="title">
                                            {{ language.trigger_message2 }}
                                        </template>
                                        <a-select disabled style="width: 400px; margin: 0 0 20px 0" optionFilterProp="label"></a-select>
                                    </a-tooltip>
                                </div>
                                <a-radio-group class="line_feed" v-model="triggerValue">
                                    <a-radio :value="1">
                                        {{ language.trigger_radio1_1 }}
                                        <a-select
                                            v-model="branchValue"
                                            mode="multiple"
                                            style="width: 400px; margin: 0 5px 0 5px"
                                            :placeholder="language.trigger_placeholder2"
                                            optionFilterProp="label"
                                            showSearch
                                        >
                                            <a-select-option
                                                v-for="(item, index) in branchList"
                                                :key="index"
                                                :value="item.name"
                                                :label="item.name"
                                            >
                                                {{ item.name }}
                                            </a-select-option>
                                        </a-select>
                                        {{ language.trigger_radio1_2 }}
                                    </a-radio>
                                    <a-radio :value="2">
                                        {{ language.trigger_radio2 }}
                                    </a-radio>
                                    <a-radio :value="3">
                                        {{ language.trigger_radio3 }}
                                    </a-radio>
                                    <a-radio :value="4">
                                        {{ language.trigger_radio4 }}
                                    </a-radio>
                                    <div v-if="triggerValue == 4" style="margin: 0 0 0 27px">
                                        <a-input
                                            :placeholder="language.trigger_placeholder3"
                                            v-model="regexpValue"
                                        ></a-input>
                                    </div>
                                </a-radio-group>
                                </a-spin>
                            </div>
                        </div>
                    </a-collapse-panel>
                </a-collapse>
            </div>

            <div class="block">
                <a-collapse activeKey="1">
                    <template #expandIcon="props">
                        <a-icon type="caret-right" :rotate="props.isActive ? 90 : 0" />
                    </template>
                    <a-collapse-panel key="1" :header="language.trigger_header2">
                        <TimerTrigger :spec.sync="spec" ref="timerTrigger"></TimerTrigger>
                    </a-collapse-panel>
                </a-collapse>
            </div>

            <div class="block">
                <a-collapse activeKey="1">
                    <template #expandIcon="props">
                        <a-icon type="caret-right" :rotate="props.isActive ? 90 : 0" />
                    </template>
                    <a-collapse-panel key="1" :header="language.trigger_header3">
                        <BuildTrigger :ReverseBuildTrigger.sync="ReverseBuildTrigger"></BuildTrigger>
                    </a-collapse-panel>
                </a-collapse>
            </div>
            <footer>
                <a-button :loading="btnLoading" @click="onsubmit" style="float: right" type="primary">{{
                    language.save
                }}</a-button>
            </footer>
        </a-spin>
    </div>
</template>

<script>
import { getProjects, getBranch } from '@/api/gitlab.js'
import { getTriggerBuildParams, editTriggerBuildParams } from '@/api/reconfig.js'
import storage from 'store'
import TimerTrigger from './timerTrigger.vue'
import BuildTrigger from './buildTrigger.vue'
export default {
    data() {
        return {
            // 是否持续集成事件发生
            isTrigger: false,
            // 持续集成的事件单选
            triggerValue: 1,
            // gitlab代码仓库
            projectsList: [],
            // 分支选项
            branchList: [],
            spinloading: false,
            // 选中的分支
            branchValue: [],
            project_id: undefined,
            hook_id: '',
            // 正则
            regexpValue: '',
            // 保存按钮
            btnLoading: false,
            spec: '',
            ReverseBuildTrigger: {},
            // 代码仓库是否正常
            gitError: false,
            canGet: false, //是否可以请求 getProjectsData 接口
            spinning1: false, //触发构建的loading
        }
    },
    created() {
        this.language = this.$store.state.language.languageAuth.pipelineConfiguration || {}
    },
    mounted() {
        this.getTriggerBuildParamsData()
    },
    methods: {
        onChange(val) {
            if(this.canGet && val) {
                this.getProjectsData()
                this.canGet = false
            }
        },
        // 触发数据整体提交到后台
        onsubmit() {
            let updata = {
                code: this.$route.query.appCode,
                job_name: this.$route.query.name,
                project_id: this.project_id,
                hook_id: this.hook_id,
                params: {
                    spec: this.spec,
                    ReverseBuildTrigger: this.ReverseBuildTrigger,
                },
                view_name:this.$route.query.view_name,
            }
            if (this.isTrigger) {
                if (!this.project_id) {
                    return this.$message.warning('请选择代码仓库')
                }
                if (this.triggerValue == 1 && this.branchValue.length == 0) {
                    return this.$message.warning('请选分支')
                }

                if (this.triggerValue == 1) {
                    updata.params.branchFilterType = 'NameBasedFilter'
                    updata.params.includeBranchesSpec = this.branchValue.join(',')
                    updata.params.push_events = 'true'
                    updata.params.tag_push_events = 'false'
                    updata.params.merge_requests_events = 'false'
                } else if (this.triggerValue == 2) {
                    updata.params.branchFilterType = 'NameBasedFilter'
                    updata.params.includeBranchesSpec = ''
                    updata.params.push_events = 'false'
                    updata.params.tag_push_events = 'true'
                    updata.params.merge_requests_events = 'false'
                } else if (this.triggerValue == 3) {
                    updata.params.branchFilterType = 'NameBasedFilter'
                    updata.params.includeBranchesSpec = ''
                    updata.params.push_events = 'false'
                    updata.params.tag_push_events = 'false'
                    updata.params.merge_requests_events = 'true'
                } else if (this.triggerValue == 4) {
                    updata.params.branchFilterType = 'RegexBasedFilter'
                    updata.params.includeBranchesSpec = ''
                    updata.params.sourceBranchRegex = this.regexpValue
                    updata.params.push_events = 'true'
                    updata.params.tag_push_events = 'false'
                    updata.params.merge_requests_events = 'false'
                }
            } else {
                updata.params.branchFilterType = 'NameBasedFilter'
                updata.params.includeBranchesSpec = null
                updata.params.sourceBranchRegex = null
                updata.params.push_events = 'false'
                updata.params.tag_push_events = 'false'
                updata.params.merge_requests_events = 'false'
            }
            if (this.ReverseBuildTrigger.threshold && !this.ReverseBuildTrigger.upstreamProjects) {
                return this.$message.warning('请选择相关流水线')
            }

            this.btnLoading = true
            editTriggerBuildParams(updata)
                .then((res) => {
                    if (res.code == 200) {
                        this.$message.success(res.message)
                        this.getTriggerBuildParamsData()
                    } else {
                        this.$message.error(res.message)
                    }
                })
                .finally(() => {
                    this.btnLoading = false
                })
        },
        // 获取gitlab项目
        getProjectsData() {
            this.spinning1 = true
            getProjects()
                .then((res) => {
                    if (res.code == 200 && res.data) {
                        this.projectsList = res.data
                    } else {
                        this.gitError = true
                    }
                })
                .catch((res) => {
                    this.gitError = true
                }).finally(()=>{
                    this.spinning1 = false
                })
        },
        // 获取分支
        getBranchData(project_id) {
            this.branchList = []
            getBranch({ project_id: project_id }).then((res) => {
                if (res.code == 200 && res.data) {
                    this.branchList = res.data
                }
            })
        },
        // gitlab代码库change
        projectsChange(val, option) {
            this.project_id = option.key
            this.getBranchData(option.key)
            this.branchValue = []
        },
        // 获取触发规则数据
        getTriggerBuildParamsData() {
            this.spinloading = true
            getTriggerBuildParams({ code: this.$route.query.appCode, job_name: this.$route.query.name, view_name:this.$route.query.view_name }).then((res) => {
                if (res.code == 200 && res.data) {
                    if (
                        res.data.push_events == 'true' ||
                        (res.data.push_events === true && res.data.branchFilterType == 'NameBasedFilter')
                    ) {
                        this.isTrigger = true
                        this.triggerValue = 1
                        this.branchValue =
                            (res.data.includeBranchesSpec && res.data.includeBranchesSpec.split(',')) || []
                    } else if (res.data.tag_push_events == 'true' || res.data.tag_push_events === true) {
                        this.isTrigger = true
                        this.triggerValue = 2
                    } else if (res.data.merge_requests_events == 'true' || res.data.merge_requests_events === true) {
                        this.isTrigger = true
                        this.triggerValue = 3
                    } else if (
                        res.data.push_events == 'true' ||
                        (res.data.push_events === true && res.data.branchFilterType == 'RegexBasedFilter')
                    ) {
                        this.isTrigger = true
                        this.triggerValue = 4
                        this.regexpValue = res.data.sourceBranchRegex
                    } else {
                        this.isTrigger = false
                    }
                    if(this.isTrigger == true) {
                        this.getProjectsData()
                        this.canGet = false
                    } else {
                        this.canGet = true
                    }

                    if (res.data.project_id) {
                        this.project_id = res.data.project_id
                        this.getBranchData(res.data.project_id)
                    }
                    this.hook_id = res.data.hook_id
                    this.spec = res.data.spec
                    this.ReverseBuildTrigger = res.data.ReverseBuildTrigger
                }
            }).finally(() => {
                this.spinloading = false
            })
        },
    },
    components: { TimerTrigger, BuildTrigger },
}
</script>

<style lang="less" scoped>
.triggerRule_main {
    color: #333;
    footer {
        border-top: 1px solid #e8e8e8;
        padding: 10px 20px;
    }
}
// 单选选项
.line_feed /deep/.ant-radio-wrapper {
    display: block;
    margin: 0 0 20px 0;
}
// 多选选项
.line_feed /deep/.ant-checkbox-group-item {
    display: block;
    margin: 0 0 10px 0;
}
// table为空提示
/deep/.ant-table-placeholder {
    padding: 0;
    .ant-empty-normal {
        margin: 10px 0 0 0;
    }
}
/deep/.ant-collapse {
    margin: 0 0 20px 0;
    border: none;
    .ant-collapse-header {
        background: #f2f2f2;
    }
    .ant-collapse-item {
        border: none;
    }
    .ant-collapse-content {
        border: none;
    }
}
</style>