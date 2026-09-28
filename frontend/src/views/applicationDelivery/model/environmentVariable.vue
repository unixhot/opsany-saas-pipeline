<template>
    <div>
        <a-drawer width="1000" title="环境变量" placement="right" :visible="visible" @close="onClose" :pagination="false">
            <a-table :columns="columns" :data-source="tableData" :pagination="false">
                <template slot="type" slot-scope="text,record">
                    <span v-if="record.value.arguments">凭据</span>
                    <span v-else>字符串</span>
                </template>

                <template slot="value" slot-scope="text,record">
                    <span v-if="record.value.arguments">{{record.value.arguments[0].value}}</span>
                    <span v-else>{{record.value.value}}</span>
                </template>

                <template slot="active" slot-scope="text,record,index">
                    <a-icon @click="addVariable(record)" style="margin:0 10px 0 0;" type="edit" />
                    <a-icon @click="deleteVariable(record,index)" type="delete" />
                </template>
            </a-table>
            <a-button @click="addVariable()" icon="plus" type="link" size="small" style="margin:10px 0 0 0">添加环境变量</a-button>

        </a-drawer>

        <a-modal :visible="visible2" @ok="onOk" @cancel="onCancel" :title="title" :maskClosable="false">
            <a-form-model ref="ruleForm" :model="formData" :rules="rules">
                <a-form-model-item label="变量名称" prop="key">
                    <a-input v-model="formData.key" placeholder="请输入变量名称" />
                </a-form-model-item>
                <a-form-model-item label="类别" prop="type">
                    <a-radio-group name="radioGroup" v-model="formData.type">
                        <a-radio :value="1">字符串</a-radio>
                        <a-radio :value="2">凭据</a-radio>
                    </a-radio-group>
                </a-form-model-item>
                <a-form-model-item v-if="formData.type==1" label="变量值" prop="value">
                    <a-input v-model="formData.value" placeholder="请输入变量值" />
                </a-form-model-item>
                <a-form-model-item v-else-if="formData.type==2" label="凭据" prop="credentials">
                    <a-tree-select v-model="formData.credentials" dropdownClassName="resource-tree-select-environmentVariable" allowClear dropdownMatchSelectWidth tree-default-expand-all showSearch treeNodeFilterProp="title" :tree-data="credentialsList" searchPlaceholder="请根据名称或唯一标识搜索" placeholder="请选择凭据" :getPopupContainer="triggerNode=>triggerNode.parentNode">
                    </a-tree-select>
                </a-form-model-item>
            </a-form-model>
        </a-modal>
    </div>
</template>

<script>
// 凭据类型的环境变量含有arguments字段,以此来判断类型
import { getCredentials } from '@/api/credential.js'

export default {
    data() {
        return {
            visible: false,
            visible2: false,
            formData: {
                key: "",
                type: 1,
                value: "",
                credentials: undefined,
            },
            rules: {
                key: [{ required: true, message: "请输入变量名称", whitespace: true, }, { validator: this.validatorKey }],
                type: [{ required: true, message: "请选择类别", }],
                credentials: [{ required: true, message: "请选择凭据", }],
            },
            columns: [
                { title: '变量名', dataIndex: 'key', width: 300, },
                { title: '类别', dataIndex: 'type', scopedSlots: { customRender: 'type' }, width: 100, },
                { title: '默认值', dataIndex: 'value', scopedSlots: { customRender: 'value' }, },
                { title: '操作', scopedSlots: { customRender: 'active' }, width: 100, align: "center" },
            ],
            tableData: [],

            isEdit: false,
            activeEnvironment: {},//修改的变量
            // 凭据选项
            credentialsList: [
                { value: "Username with password", title: "密码验证", children: [] },
                { value: "GitLab API token", title: "GitLab令牌", children: [] },
                { value: "SSH Username with private key", title: "密钥验证", children: [] },
                { value: "Secret text", title: "密钥文本", children: [] },
            ],
            title: "",
        }
    },
    methods: {
        onShow(environment) {
            console.log(environment)
            this.visible = true
            this.tableData = environment
            this.getCredentialsData()
        },
        onClose() {
            this.visible = false
        },
        onOk() {
            this.$refs.ruleForm.validate(vali => {
                if (vali) {
                    if (this.isEdit) {
                        if (this.formData.type == 1) {
                            this.activeEnvironment.key = this.formData.key
                            this.activeEnvironment.value = { isLiteral: true, value: this.formData.value, }
                        } else {
                            this.activeEnvironment.key = this.formData.key
                            this.activeEnvironment.value = {
                                name: "credentials", arguments: [{ isLiteral: true, value: this.formData.credentials, }],
                            }
                        }
                    } else {

                        let flag = this.tableData.find(item => {
                            return item.key == this.formData.key
                        })
                        if (flag) {
                            return this.$message.warning("该变量名已存在,请修改后重试。")
                        }


                        if (this.formData.type == 1) {
                            this.tableData.push({ key: this.formData.key, value: { isLiteral: true, value: this.formData.value, } })
                        } else {
                            this.tableData.push({
                                key: this.formData.key, value: {
                                    name: "credentials", arguments: [{ isLiteral: true, value: this.formData.credentials, }],
                                }
                            })
                        }
                    }
                    this.onCancel()
                }
            })

        },
        onCancel() {
            this.formData = this.$options.data().formData
            this.$refs.ruleForm.resetFields()
            this.visible2 = false
        },
        addVariable(record) {
            this.visible2 = true
            this.activeEnvironment = record
            this.$nextTick(() => {
                if (record) {
                    this.isEdit = true
                    this.title = "修改变量"
                    let obj = JSON.parse(JSON.stringify(record))
                    if (obj.value.arguments) {
                        this.formData = { key: obj.key, type: 2, credentials: obj.value.arguments[0].value, }
                    } else {
                        this.formData = { key: obj.key, type: 1, value: record.value.value, }
                    }
                } else {
                    this.isEdit = false
                    this.title = "添加变量"
                }
            })
        },
        deleteVariable(record, index) {
            console.log(record, index)
            this.tableData.splice(index, 1)
        },
        // 获取凭据
        getCredentialsData() {
            return getCredentials({
                app_code: this.$route.query.appCode,
                all_data: 'true',
            }).then((res) => {
                if (res.code == 200 && res.data) {
                    res.data.forEach(item => {
                        item.value = item.credentials_id
                        item.key = item.credentials_id
                        item.title = `${item.name}(${item.credentials_id})`
                        let obj = this.credentialsList.find(ele => {
                            ele.selectable = false
                            return ele.value == item.typeName
                        })
                        if (obj) {
                            obj.children.push(item)
                        }
                    })
                }
            })
        },
        validatorKey(rule, value, callback) {
            let reg = /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/
            if (!reg.test(this.formData.key)) {
                callback("变量名只能输入数字、字母、下划线")
            } else {
                callback()
            }
        }
    },
}
</script>
<style lang="less" scoped>
.environment_list {
	display: flex;
	align-items: center;
	margin: 0 0 10px 0;
	.environment_box {
		display: flex;
	}
}

.equal {
	border: 1px solid #d9d9d9;
	width: 40px;
	line-height: 30px;
	display: inline-block;
	text-align: center;
}
</style>
<style lang="less">
.resource-tree-select-environmentVariable {
    max-height: 400px !important;
}
</style>
<style>
.resource-tree-select-environmentVariable .ant-select-tree-switcher {
	position: relative;
}
.resource-tree-select-environmentVariable .ant-select-tree-switcher_open::before,
.resource-tree-select-environmentVariable .ant-select-tree-switcher_close::before {
	content: "";
	position: absolute;
	right: -420px;
	top: 0;
	left: 0;
	bottom: 0;
}
</style>