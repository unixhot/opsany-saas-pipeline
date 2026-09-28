<template>
    <!-- processConfiguration 流程配置 -->
    <div>
        <a-spin :spinning="spinLoading">
            <a-radio-group v-if="show" @change="onPipelineTypeChange" v-model="pipelineType" style="margin: 8px 0">
                <a-radio-button value="graphical">
                    {{language.process_radioList1}}
                </a-radio-button>
                <a-radio-button value="text">
                    {{language.process_radioList2}}
                </a-radio-button>
            </a-radio-group>

            <div v-if="pipelineType=='text'">
                <code-format style="margin-top:10px;" ref="codeFormat" v-model="content"></code-format>
            </div>
            <div v-else-if="pipelineType=='graphical'">
                <GraphicEditing :btnLoading.sync="btnLoading" ref="GraphicEditing" @subtofatherPepiline="editContent" :fathertosubpipelineJson.sync="pipelineJson"></GraphicEditing>
            </div>
            <footer>
                <a-button :loading="btnLoading" type="primary" style="float:right" @click="handle">保存</a-button>
            </footer>
        </a-spin>
    </div>
</template>

<script>
import { getReconfig, editReconfig } from "@/api/reconfig"
import { checkSyntax, toJson } from "@/api/jenkinsTransform"
import GraphicEditing from "./graphicEditing.vue"
import storage from 'store'
export default {
    data() {
        return {
            pipelineType: "text",
            content: '',
            pipelineJson: {},
            show: true,
            spinLoading: true,
            btnLoading: false,
        }
    },
    created() {
        this.language = this.$store.state.language.languageAuth.pipelineConfiguration || {}
    },
    mounted() {
        this.getReconfigData()
        // this.pipelineType="graphical"
    },
    methods: {
        // 切换图形or文本编辑(点击后并不立即切换,先进性json和ppipeline之间的转换，接口无误后图形或文本编辑切换)
        onPipelineTypeChange(e) {
            if (e.target.value == "text") {
                this.pipelineType = "graphical"
                this.$refs.GraphicEditing.toPepiline()
            } else if (e.target.value == "graphical") {
                this.pipelineType = "text"
                this.tojson()
            }
        },
        // pipeline转json
        tojson() {
            let formdata = new FormData();
            formdata.append("jenkins_file", this.content)
            // checkSyntax(formdata)
            toJson(formdata).then(res => {
                if (res.code == 200 && res.data) {
                    this.pipelineJson = res.data
                    this.pipelineType = "graphical"
                }
            }).catch(() => {
                this.pipelineType = "text"
                this.show = false
                this.$nextTick(function () {
                    this.show = true
                })
            }).finally(() => {
                this.spinLoading = false
            })
        },
        // 获取配置信息
        getReconfigData() {
            getReconfig({ code: this.$route.query.appCode, job_name: this.$route.query.name }).then(res => {
                if (res.data) {
                    this.content = res.data
                    this.tojson()
                } else {
                    this.spinLoading = false
                }
            })
        },
        // 保存
        handle() {
            this.btnLoading = true
            if (this.pipelineType == "graphical") {
                this.$refs.GraphicEditing.toPepiline(true)
            } else if (this.pipelineType == "text") {
                editReconfig({ code: this.$route.query.appCode, job_name: this.$route.query.name, jenkins_file: this.content }).then(res => {
                    if (res.code == 200) {
                        this.$message.success(res.message)
                    } else {
                        this.$message.error(res.message)
                    }
                }).finally(() => {
                    this.btnLoading = false
                })
            }

        },
        editContent(contentData, success) {
            if (success) {
                this.content = contentData
            }
            this.pipelineType = "text"
            this.btnLoading = false
            // if (success) {
            //     this.pipelineType = "text"
            // } else {
            //     this.pipelineType = "graphical"
            //     this.show = false
            //     this.$nextTick(function () {
            //         this.show = true
            //     })
            // }
        }
    },
    components: {
        GraphicEditing,
    }
}
</script>

<style lang="less" scoped>
/deep/.ant-spin-blur::after {
    opacity: 1;
}
footer {
    border-top: 1px solid #e8e8e8;
    padding: 10px 20px;
    margin: 10px 0 0 0;
}
</style>>