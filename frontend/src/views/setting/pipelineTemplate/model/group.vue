<template>
    <div>
        <a-modal :title="activeGroup&&activeGroup.code? language.group_title1 : language.group_title2" :confirmLoading="btnLoading" v-model="groupModel" @ok="handleOk">
            <a-form :form="groupForm" :label-col="{span:5}" :wrapper-col="{span:16}">
                <a-form-item :label="language.group_label" required>
                    <a-input v-decorator="[
                            'name',
                            {
                                rules: [{ required: true, message: language.group_placeholder }],
                                
                            }
                        ]" :placeholder="language.group_placeholder" />
                </a-form-item>
            </a-form>
        </a-modal>
    </div>
</template>

<script>
import { addPipelineTemplateGroup, editPipelineTemplateGroup } from "@/api/pipelineTemplate.js"
export default {
    data() {
        return {
            // 弹框是否显示
            groupModel: false,
            groupForm: this.$form.createForm(this, { name: "groupForm" }),
            // 确定按钮loading
            btnLoading: false,
            //操作的分组
            activeGroup: {},
            deployType: "",
        }
    },
    methods: {
        show(record, deployType) {
            this.groupModel = true
            this.groupForm.resetFields()
            if (record) {
                this.activeGroup = record
                this.$nextTick(function () {
                    this.groupForm.setFieldsValue({
                        name: record.name
                    })
                })
            } else {
                this.activeGroup = {}
                this.deployType = deployType
            }
        },
        handleOk() {
            this.groupForm.validateFields((err, val) => {
                if (!err) {
                    this.btnLoading = true
                    if (this.activeGroup && this.activeGroup.code) {
                        editPipelineTemplateGroup({ code: this.activeGroup.code, name: val.name, built_in: this.activeGroup.built_in }).then(res => {
                            if (res.code == 200) {
                                this.$message.success(res.message)
                                this.groupModel = false
                                this.$emit("father")
                            } else {
                                this.$message.error(res.message)
                            }
                        }).finally(() => {
                            this.btnLoading = false
                        })
                    } else {
                        addPipelineTemplateGroup({ name: val.name, built_in: this.deployType == "inner" }).then(res => {
                            if (res.code == 200) {
                                this.$message.success(res.message)
                                this.groupModel = false
                                this.$emit("father")
                            } else {
                                this.$message.error(res.message)
                            }
                        }).finally(() => {
                            this.btnLoading = false
                        })
                    }
                }
            })
        }
    },
    created(){
        this.language = this.$store.state.language.languageAuth.pipelineTemplate || {}
    },
}
</script>

<style lang="less" scoped>
</style>