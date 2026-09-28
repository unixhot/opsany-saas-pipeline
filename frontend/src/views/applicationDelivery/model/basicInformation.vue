<template>
    <!-- basicInformation 基础信息 -->
    <div class="main">
        <a-spin :spinning="spinLoading">
            <a-form :form="basicInformationForm" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
                <a-form-item :label="language.basic_label1">
                    <a-input :placeholder="language.basic_placeholder1" v-decorator="['name', { rules: [{ required: true,pattern:/^[0-9a-zA-Z-_]{1,}$/, message: language.basic_placeholder1 },
                    { max: 50,message: '流水线名称长度限制在50个字符以内。',}] }]"></a-input>
                </a-form-item>
                <a-form-item :label="language.basic_label2">
                    <a-tree-select treeNodeFilterProp="title" disabled v-decorator="['code', { rules: [{ required: true, message: '请选择所属应用'}] }]" showSearch :treeData="treeData" style="width: 100%" placeholder="请选择所属应用" tree-default-expand-all>
                    </a-tree-select>
                </a-form-item>
                <a-form-item :label="language.basic_label3">
                    <a-textarea :placeholder="language.basic_placeholder3" :rows="6" v-decorator="['description', { rules: [{ required: false,max:100, message: '长度不能超过100字' }] }]"></a-textarea>
                </a-form-item>
                <a-form-item :label="language.basic_label4">
                    <a-switch v-model="isretain">{{language.basic_label4}}</a-switch>
                    <div v-show="isretain">
                        <a-form :form="retainForm" labelAlign="left" :label-col="{ span: 20 }" :wrapper-col="{ span: 14 }">
                            <!-- <a-form-item :label="language.label5">
                                <a-select style="width:500px;" v-decorator="['strategy', { initialValue:'Log Rotation',rules: [{ required: true, message: '请输入名称' }] }]">
                                    <a-select-option value="Log Rotation">Log Rotation</a-select-option>
                                </a-select>
                            </a-form-item> -->
                            <a-form-item class="align_left" :label="language.label6">
                                <a-input-number :placeholder="language.basic_placeholder6" style="width:300px;" :min="1" v-decorator="['daysToKeep', { rules: [{ required: false, message: '请输入保持构建的天数' }] }]"></a-input-number>
                            </a-form-item>
                            <a-form-item class="align_left" :label="language.label7">
                                <a-input-number :placeholder="language.basic_placeholder7" style="width:300px;" :min="1" v-decorator="['numToKeep', { rules: [{ required: false, message: '请输入保持构建的最大个数' }] }]"></a-input-number>
                            </a-form-item>

                        </a-form>
                    </div>
                </a-form-item>
            </a-form>

            <a-button :loading="btnLoading" @click="preserve" style="float:right;margin:20px 120px 0 0" type="primary">{{language.save}}</a-button>
        </a-spin>
    </div>
</template>

<script>
import { getBasicInformation, editAssemblyLine } from "@/api/assemblyLine.js"
import storage from 'store'
import { getBusinessTree } from '@/api/business.js'
export default {
    data() {
        return {
            basicInformationForm: this.$form.createForm(this, { name: 'basicInformationForm' }),
            retainForm: this.$form.createForm(this, { name: 'retainForm' }),
            btnLoading: false,
            spinLoading: true,
            // 是否选择构建保留策略
            isretain: false,
            treeData: [],
            otherAppUrl: window.API_ROOT.replace('/pipeline', ''),
        }
    },
    created() {
        this.language = this.$store.state.language.languageAuth.pipelineConfiguration || {}
    },
    mounted() {
        this.getBasicInformationData()
        this.getBusinessTreeData()
    },
    methods: {
        // 获取业务与应用
        getBusinessTreeData() {
            getBusinessTree().then(res => {
                if (res.data) {
                    this.treeData = res.data
                    this.treeData = res.data.filter(item => {
                        return item.children && item.children.length > 0
                    })
                    this.treeData.map(item => {
                        item.key = "n" + item.code
                        item.value = "n" + item.code
                        item.title = item.name
                        item.disabled = true
                        item.children.map(ele => {
                            ele.key = ele.code + ""
                            ele.value = ele.code + ""
                            ele.title = ele.name
                        })
                    })
                }
            })
        },
        // 提交保存
        preserve() {
            this.basicInformationForm.validateFields((err, values) => {
                if (!err) {
                    let updata = {
                        code: this.$route.query.appCode,
                        name: this.$route.query.name, rename: this.basicInformationForm.getFieldValue("name"),
                        description: this.basicInformationForm.getFieldValue("description"),
                        view_name:this.$route.query.view_name,
                    }
                    let flag
                    if (this.isretain) {
                        this.retainForm.validateFields((error, val) => {
                            if (!error) {
                                updata.build_discard = val
                                updata.build_discard.strategy = "Log Rotation"
                            } else {
                                flag = true
                            }
                        })
                    }
                    if (flag) {
                        return false
                    }
                    this.btnLoading = true
                    editAssemblyLine(updata).then(res => {
                        if (res.code == 200) {
                            this.$message.success(res.message)
                            this.$route.query.name = this.basicInformationForm.getFieldValue("name")
                        } else {
                            this.$message.error(res.message)
                        }
                    }).finally(() => {
                        this.btnLoading = false
                    })

                }
            })
        },
        // 获取数据并回显
        getBasicInformationData() {
            getBasicInformation({ job_name: this.$route.query.name, code: this.$route.query.appCode }).then(res => {
                if (res.code == 200 && res.data) {
                    this.basicInformationForm.setFieldsValue({ name: res.data.name, description: res.data.description,code:this.$route.query.appCode })
                    this.spinLoading = false
                    if (res.data.build_discard) {
                        this.isretain = true
                        this.retainForm.setFieldsValue({ daysToKeep: res.data.build_discard.daysToKeep, numToKeep: res.data.build_discard.numToKeep })
                    }
                }
            })
        }
    }
}
</script>

<style lang="less" scoped>
.main {
    /deep/.ant-card-head {
        background: rgba(248, 248, 249, 1);
    }
    .ant-card-bordered {
        width: calc(75% + 83px);
        margin-left: calc(16.7% - 83px);
        /deep/.align_left {
            .ant-form-item-label {
                text-align: left;
                margin-left: calc(12.5%);
                width: 150px;
            }
        }
    }
}
</style>