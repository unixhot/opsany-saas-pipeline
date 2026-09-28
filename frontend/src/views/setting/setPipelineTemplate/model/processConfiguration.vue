<template>
    <!-- processConfiguration 流程配置 -->
    <div>
        <a-spin :spinning="spinLoading">
        <a-radio-group v-if="show" @change="onPipelineTypeChange" v-model="pipelineType" style="margin:8px 0">
            <a-radio-button value="graphical">
                图形化编辑
            </a-radio-button>
            <a-radio-button value="text">
                文本编辑
            </a-radio-button>
        </a-radio-group>
        
        <div v-if="pipelineType=='text'">
            <code-format style="margin-top:10px;" ref="codeFormat" v-model="content"></code-format>
        </div>
        <div v-else-if="pipelineType=='graphical'">
            <GraphicEditing ref="GraphicEditing" @subtofatherPepiline="editContent" :fathertosubpipelineJson.sync="pipelineJson"></GraphicEditing>
        </div>
        </a-spin>
    </div>
</template>

<script>

import { checkSyntax, toJson } from "@/api/jenkinsTransform"
import GraphicEditing from "./graphicEditing.vue"

export default {
    data() {
        return {
            pipelineType: "text",
            content: '',
            pipelineJson: {},
            show: true,
            spinLoading:true,
        }
    },
    props: ["templateData"],
    watch: {
        templateData(val, oldval) {
            this.content = val.template
            this.tojson()
        }
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
            }).finally(()=>{
                this.spinLoading=false
            })
        },
        // 保存
        handle() {
            if (this.pipelineType == "graphical") {
                return this.$refs.GraphicEditing.toPepiline(true)
            } else if (this.pipelineType == "text") {
                let formData = new FormData()
                formData.append("jenkins_file", this.content)
                return checkSyntax(formData).then(res => {
                    if (res.code == 200) {
                        // this.$message.success(res.message)

                    } else {
                        this.$message.error(res.message)
                    }
                })
            }

        },
        editContent(contentData, success) {
            if (success) {
                this.content = contentData
            }
            this.pipelineType = "text"
            this.btnLoading = false
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
</style>>