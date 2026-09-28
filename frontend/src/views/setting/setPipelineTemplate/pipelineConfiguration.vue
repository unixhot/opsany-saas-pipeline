<template>
    <!-- pipelineConfiguration 流水线配置 -->
    <div class="main">
        <header>
            <p style="font-size:20px;margin:0;">
                <a-icon type="arrow-left" @click="$router.go(-1)" style="margin:0 20px 0 0;color:#09f;cursor:pointer" /><span>模板配置</span>
                <a-button :loading="btnLoading" @click="handel" type="primary" style="float:right">保存</a-button>
            </p>
        </header>
        <div class="main-content">
            <a-tabs v-model="tabIndex" @change="callback">
                <a-tab-pane :key="1" tab="基础信息">

                </a-tab-pane>

                <a-tab-pane :key="2" tab="流程配置" force-render>
                </a-tab-pane>
            </a-tabs>
            <BasicInformation ref="BasicInformation" v-show="tabIndex==1" :templateData.sync="templateData"></BasicInformation>
            <ProcessConfiguration ref="ProcessConfiguration" v-show="tabIndex==2" :templateData.sync="templateData"></ProcessConfiguration>

        </div>
    </div>
</template>

<script>
import { toJson, checkSyntax } from "@/api/jenkinsTransform.js"
import BasicInformation from "./model/basicInformation.vue"
import ProcessConfiguration from "./model/processConfiguration.vue"
import { getTemplate, editTemplate, addTemplate } from "@/api/pipelineTemplate.js"
export default {
    data() {
        return {
            templateData: {},
            tabIndex: 1,
            // 保存按钮loading
            btnLoading: false
        }
    },
    mounted() {
        if (this.$route.query.code) {
            this.getTemplateData(this.$route.query.code)
        } else {
            this.templateData = { template: "pipeline {\n  agent any\n  stages {\n    stage('Hello OpsAny') {\n      steps {\n        echo 'Hello OpsAny'\n      }\n    }\n\n  }\n}" }
        }
    },
    methods: {
        callback(index) {
            this.tabIndex = index
        },
        getTemplateData(code) {
            getTemplate({ code: code }).then(res => {
                if (res.code == 200 && res.data) {
                    this.templateData = res.data
                }
            })
        },
        handel() {
            this.$refs.BasicInformation.basicInformationForm.validateFields((err, values) => {
                if (!err) {
                    this.btnLoading = true
                    this.$refs.ProcessConfiguration.handle().then(() => {
                        let content = this.$refs.ProcessConfiguration.content
                        let built_in = window.sessionStorage.getItem("is_inner_pipeline") == "true" ? true : false
                        let updata = {
                            built_in: built_in,
                            group_id: values.group_id,
                            name: values.name,
                            description: values.description,
                            template: content
                        }
                        if (this.$route.query.code) {
                            updata.code = this.$route.query.code
                            editTemplate(updata).then(res => {
                                if (res.code == 200) {
                                    this.$message.success(res.message)
                                    this.$router.go(-1)
                                } else {
                                    this.$message.error(res.message)
                                }
                            }).catch(res => {
                                this.callback(2)
                            })
                        } else {
                            addTemplate(updata).then(res => {
                                if (res.code == 200) {
                                    this.$message.success(res.message)
                                    this.$router.go(-1)
                                } else {
                                    this.$message.error(res.message)
                                }
                            }).catch(res => {
                                this.callback(2)
                            })
                        }
                    }).catch(res => {
                        this.callback(2)
                    })
                        .finally(() => {
                            this.btnLoading = false
                        })
                } else {
                    this.callback(1)
                }
            })
        }
    },
    components: {
        BasicInformation,
        ProcessConfiguration
    }
}
</script>

<style scoped lang="less">
.main {
    background: #fff;
    header {
        border-bottom: 1px solid #ccc;
        padding: 20px;
    }
    .main-content {
        padding: 20px;
    }
}
</style>