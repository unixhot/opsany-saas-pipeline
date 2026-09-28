<template>
    <div>
        <a-drawer
            width="720"
            :body-style="{ width: '700px' }"
            :title="drawerTitle"
            @close="onClose"
            placement="right"
            :visible="credentialVisible"
        >
            <a-form :form="credentialForm" :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
                <a-form-item v-if="isadd" :label="language.leabel1">
                    <a-select
                        style="width: 500px"
                        @change="storageTypeChange"
                        v-decorator="['storage_type', { rules: [{ required: true, message: '请选择存储方式' }] }]"
                        optionFilterProp="label"
                        showSearch
                    >
                        <a-select-option
                            v-for="(item, index) in credentialsTypeList"
                            :value="item.name"
                            :key="index"
                            :label="item.name"
                            >{{ item.name }}</a-select-option
                        >
                    </a-select>
                </a-form-item>

                <a-form-item v-if="isadd" :label="language.leabel2">
                    <a-select
                        style="width: 500px"
                        @change="typeChange"
                        v-decorator="['type', { rules: [{ required: true, message: '请选择类型' }] }]"
                        optionFilterProp="label"
                        showSearch
                    >
                        <a-select-option
                            v-for="(item, index) in typeList"
                            :value="item.id"
                            :key="index"
                            :label="item.ch_name"
                            >{{ item.ch_name }}</a-select-option
                        >
                    </a-select>
                </a-form-item>

                <a-form-item :label="language.leabel3">
                    <a-select
                        @change="innerChange"
                        :placeholder="language.placeholder3"
                        style="width: 500px"
                        v-decorator="['is_inner', { rules: [{ required: true, message: language.placeholder3 }] }]"
                    >
                        <a-select-option value="true">{{ language.selectOption1 }}</a-select-option>
                        <a-select-option value="false">{{ language.selectOption2 }}</a-select-option>
                    </a-select>
                </a-form-item>
                <a-form-item v-if="is_inner == 'true' || is_inner == true" label="关联应用">
                    <a-tree-select dropdownClassName="resource-tree-select-addCredential" allowClear tree-default-expand-all showSearch treeNodeFilterProp="title" :tree-data="treeData" placeholder="请选择所属应用"
                        style="width: 400px" dropdownMatchSelectWidth v-decorator="['app_code', { rules: [{ required: true, message: '请选择所属应用' }] }]">
                    </a-tree-select>
                    <a-button @click="getBusinessTreeData" :loading="btnLoading2" icon="reload" type="link"></a-button>
                    <a target="_blank" :href="otherAppUrl + 'devops/#/configure/application'">去创建</a>
                </a-form-item>

                <template v-for="(value, key) in fieldsList">
                    <a-form-item v-if="key == 'credentials_id'" :key="key" :label="language.leabel4">
                        <a-input
                            :placeholder="language.placeholder4"
                            style="width: 450px;margin:0 10px 0 0;"
                            :disabled="!isadd"
                            v-decorator="[key, { rules: [{ required: true, message: language.placeholder4 }] }]"
                        ></a-input>
                        <a v-if="isadd" @click="uuid">生成</a>
                    </a-form-item>
                    <a-form-item v-else-if="key == 'name'" :key="key" :label="language.leabel5">
                        <a-input
                            :placeholder="language.placeholder5"
                            style="width: 500px"
                            v-decorator="[key, { rules: [{ required: true, message: language.placeholder5 }] }]"
                        ></a-input>
                    </a-form-item>

                    <a-form-item v-else-if="key == 'username'" :key="key" :label="language.leabel6">
                        <a-input
                            :placeholder="language.placeholder6"
                            style="width: 500px"
                            v-decorator="[key, { rules: [{ required: false }] }]"
                        ></a-input>
                    </a-form-item>
                    <a-form-item v-else-if="key == 'description'" :key="key" :label="language.leabel7">
                        <a-input
                            :placeholder="language.placeholder7"
                            style="width: 500px"
                            v-decorator="[key, { rules: [{ required: false }] }]"
                        ></a-input>
                    </a-form-item>

                    <a-form-item
                        v-else-if="key == 'password' || key == 'passphrase' || key == 'apiToken' || key =='secret' "
                        :key="key"
                        :label="passLabel(key)"
                    >
                        <template v-if="isadd">
                            <a-input-password
                                :placeholder="passPlaceholder(key)"
                                style="width: 500px"
                                v-decorator="[key, { rules: [{ required: false }] }]"
                            ></a-input-password>
                        </template>
                        <template v-else>
                            <a-input-password
                                v-if="passworldShow"
                                :placeholder="passPlaceholder(key)"
                                style="width: 500px; vertical-align: middle"
                                v-decorator="[
                                    key,
                                    {
                                        rules: [
                                            {
                                                required: false,
                                                message:passPlaceholder(key)
                                            },
                                        ],
                                    },
                                ]"
                            ></a-input-password>
                            <a-input v-else style="width: 500px" disabled value="**************"></a-input>
                            <a
                                style="vertical-align: middle; margin: 0 0 0 5px"
                                @click="passworldShow = !passworldShow"
                                >{{ passworldShow ? language.giveUp : language.edit }}</a
                            >
                        </template>
                    </a-form-item>

                    <a-form-item v-else-if="key == 'privateKey'" :key="key" :label="language.leabel9">
                        <template v-if="isadd">
                            <a-textarea
                                :placeholder="language.placeholder9"
                                :rows="6"
                                v-decorator="[key, { rules: [{ required: false }] }]"
                            ></a-textarea>
                        </template>
                        <template v-else>
                            <a-textarea
                                :placeholder="language.placeholder9"
                                v-if="secretkeyShow"
                                style="width: 500px; vertical-align: middle"
                                :rows="6"
                                v-decorator="[key, { rules: [{ required: false, message: language.placeholder9 }] }]"
                            ></a-textarea>
                            <a-textarea
                                value="***********************************************************************************************************"
                                disabled
                                v-else
                                style="width: 500px; vertical-align: middle"
                                :rows="6"
                            ></a-textarea>
                            <a
                                style="vertical-align: middle; margin: 0 0 0 5px"
                                @click="secretkeyShow = !secretkeyShow"
                                >{{ secretkeyShow ? language.giveUp : language.edit }}</a
                            >
                        </template>
                    </a-form-item>
                </template>
            </a-form>
            <div class="footer">
                <a-button @click="onClose">{{ language.cancel }}</a-button>
                <a-button :loading="btnLoading" @click="onSubmit" style="margin: 0 0 0 10px" type="primary">{{
                    language.ok
                }}</a-button>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import { addCredentials, editCredentials } from '@/api/credential.js'
import { getBusinessTree } from "@/api/business.js"

export default {
    data() {
        return {
            credentialVisible: false,
            credentialForm: this.$form.createForm(this, { name: 'credentialForm' }),
            // 类型选项
            typeList: [
                // { name: "密码验证", value: "0" }, { name: "秘钥", value: "4" }
            ],
            // 字段
            fieldsList: [],
            // 添加或修改
            isadd: true,
            // 选中的凭据
            credential: {},
            // 提交按钮loading
            btnLoading: false,
            // 修改时paddword  input是否显示
            passworldShow: false,
            secretkeyShow: false,
            drawerTitle: '新建凭据',
            is_inner: false,
            treeData: [],
            btnLoading2: false,
            otherAppUrl: window.API_ROOT.replace('/pipeline', ''),
        }
    },
    props: ['credentialsTypeList'],
    created() {
        this.language = Object.assign(
            {},
            this.$store.state.language.languageAuth.public1 || {},
            this.$store.state.language.languageAuth.credentialManagement || {}
        )
    },
    methods: {
        passLabel(val) {
            if(val == 'passphrase') {
                return this.language.leabel8_2
            } else if(val == 'password') {
                return this.language.leabel8_2
            } else if(val == 'apiToken') {
                return this.language.leabel8_3
            } else if(val == 'secret') {
                return this.language.leabel8_4
            } 
        },
        passPlaceholder(val) {
            if(val == 'passphrase') {
                return this.language.placeholder8_2
            } else if(val == 'password') {
                return this.language.placeholder8_2
            } else if(val == 'apiToken') {
                return this.language.placeholder8_3
            } else if(val == 'secret') {
                return this.language.placeholder8_4
            } 
        },
        uuid() {
            const { v4: uuidv4 } = require('uuid');
            const uuid = uuidv4();
            this.credentialForm.setFieldsValue({
                credentials_id: uuid,
            })
        },
        // 打开抽屉
        show(record) {
            this.getBusinessTreeData()
            this.credentialVisible = true
            this.credential = record
            this.credentialForm.resetFields()
            // console.log(this.credentialsTypeList[0])
            if (record) {
                this.drawerTitle = this.language.drawerTitle1
                this.isadd = false
                this.typeList = this.credentialsTypeList.find((item) => {
                    return item.name == record.storage_type
                }).type_list
                console.log(this.typeList,record.type)
                this.fieldsList = this.typeList.find((item) => {
                    return item.id == record.type
                }).fields
                console.log(this.fieldsList)
                this.is_inner = record.is_inner
                this.$nextTick(() => {
                    this.credentialForm.setFieldsValue({
                        // storage_type: record.storage_type,
                        // type: record.type,
                        is_inner: record.is_inner + '',
                    })
                    if(record.application?.code) {
                        this.credentialForm.setFieldsValue({
                            app_code: record.application?.code
                        })
                    }
                    for (var key in this.fieldsList) {
                        this.credentialForm.setFieldsValue({ [key]: record[key] })
                    }
                })
            } else {
                this.drawerTitle = this.language.drawerTitle2
                this.isadd = true
                this.typeList = this.credentialsTypeList[0].type_list
                this.fieldsList = this.typeList[0].fields
                console.log(this.fieldsList)
                this.$nextTick(() => {
                    this.credentialForm.setFieldsValue({
                        storage_type: this.credentialsTypeList[0].name,
                        type: this.typeList[0].id,
                    })
                })
            }
        },
        // 关闭
        onClose() {
            this.credentialVisible = false
            this.passworldShow = false
            this.secretkeyShow = false
        },
        // 提交
        onSubmit() {
            this.credentialForm.validateFields((err, values) => {
                if (!err) {
                    this.btnLoading = true
                    let updata = {
                        params: { ...values },
                        storage_type: values.storage_type,
                        type: values.type,
                        name: values.name,
                        is_inner: values.is_inner == "true",
                        app_code: values.app_code,
                    }
                    delete updata.params.storage_type
                    delete updata.params.type
                    delete updata.params.name
                    delete updata.params.is_inner
                    if (this.isadd) {
                        addCredentials(updata)
                            .then((res) => {
                                if (res.code == 200) {
                                    this.$message.success(res.message)
                                    this.onClose()
                                    this.$emit('father')
                                } else {
                                    this.$message.error(res.message)
                                }
                            })
                            .finally(() => {
                                this.btnLoading = false
                            })
                    } else {
                        updata.code = this.credential.code
                        editCredentials(updata)
                            .then((res) => {
                                if (res.code == 200) {
                                    this.$message.success(res.message)
                                    this.onClose()
                                    this.$emit('father')
                                } else {
                                    this.$message.error(res.message)
                                }
                            })
                            .finally(() => {
                                this.btnLoading = false
                            })
                    }
                }
            })
        },
        // 存储方式change
        storageTypeChange(val) {
            let storage1 = this.credentialsTypeList.find((item) => {
                return item.name == val
            })
            this.typeList = storage1.type_list
        },
        typeChange(val) {
            let type = this.typeList.find((item) => {
                return item.id == val
            })
            this.fieldsList = type.fields
        },
        innerChange(val) {
            this.is_inner = val
        },
        // 获取业务与应用
        getBusinessTreeData() {
            this.btnLoading2 = true
            getBusinessTree().then((res) => {
                if (res.data) {
                    this.treeData = res.data
                    this.treeData = res.data.filter((item) => {
                        return item.children && item.children.length > 0
                    })
                    this.treeData.map((item) => {
                        item.key = 'n' + item.code
                        item.value = 'n' + item.code
                        item.title = item.name
                        item.selectable = false
                        item.children.map((ele) => {
                            ele.key = ele.code + ''
                            ele.value = ele.code + ''
                            ele.title = ele.name
                        })
                    })
                }
            }).finally(()=>{
               this.btnLoading2 = false
            })
        },
    },
}
</script>

<style lang="less" scoped>
.footer {
    float: right;
    margin: 0 20px 0 0;
}
</style>

<style lang="less">
.resource-tree-select-addCredential {
    max-height: 400px !important;
}
</style>

<style>
.resource-tree-select-addCredential .ant-select-tree-switcher {
	position: relative;
}
.resource-tree-select-addCredential .ant-select-tree-switcher_open::before,
.resource-tree-select-addCredential .ant-select-tree-switcher_close::before {
	content: "";
	position: absolute;
	right: -360px;
	top: 0;
	left: 0;
	bottom: 0;
}
</style>