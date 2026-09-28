<template>
    <div>
        <!-- Parameter setting 参数设置 -->
        <h3 style="font-weight: 1000">{{language.parameter_title}}</h3>
        <p>{{language.parameter_message}}</p>
        <a-table :loading="tableLoading" :pagination="false" :columns="columns" :data-source="tableData">
            <span slot="action" slot-scope="record">
                <a @click="parameterSettingShow(record)">{{language.edit}}</a>
                <a @click="deleted(record)" style="color: red; margin: 0 0 0 10px">{{language.delete}}</a>
            </span>
        </a-table>
        <a
            @click="parameterSettingShow()"
            style="color: @primary-color; margin: 10px 0 0 0; font-size: 18px; display: inline-block"
        >
            <a-icon style="margin: 0 10px 0 0" theme="filled" type="plus-circle" />{{language.parameter_modal_title1}}
        </a>
        <footer>
            <a-button :loading="btnLoading" @click="onSunmit" type="primary">{{language.save}}</a-button>
        </footer>

        <a-modal width="800px" @ok="handleOk" v-model="parameterSettingModel" :title="isadd ? language.parameter_modal_title1 : language.parameter_modal_title2">
            <a-form :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }" :form="parameterSettingForm">
                <a-form-item :label="language.parameter_label1">
                    <a-input
                        :disabled="!isadd"
                        :placeholder="language.parameter_placeholder1"
                        v-decorator="[
                            'name',
                            {
                                rules: [
                                    {
                                        required: true,
                                        pattern: '^[a-zA-Z_][A-Za-z0-9_]*$',
                                        message: language.parameter_rule,
                                    },
                                ],
                            },
                        ]"
                    ></a-input>
                </a-form-item>
                <a-form-item :label="language.parameter_label2">
                    <a-select
                        :disabled="!isadd"
                        :placeholder="language.parameter_placeholder2"
                        @change="typechange"
                        v-decorator="[
                            'paramsType',
                            { initialValue: 'string', rules: [{ required: true, message: language.parameter_placeholder2 }] },
                        ]"
                    >
                        <a-select-option value="string">{{language.parameter_option1}}</a-select-option>
                        <a-select-option value="select">{{language.parameter_option2}}</a-select-option>
                    </a-select>
                </a-form-item>
                <a-form-item v-if="paramsType == 'string'" :label="language.parameter_label3">
                    <a-input
                        :placeholder="language.parameter_placeholder3"
                        v-decorator="['default_string', { rules: [{ required: false, message: language.parameter_placeholder3 }] }]"
                    ></a-input>
                </a-form-item>
                <a-form-item v-else :label="language.parameter_label4">
                    <a-input
                        :placeholder="language.parameter_placeholder4"
                        @change="inputchange"
                        v-for="(item, index) in selectList"
                        :key="index"
                        v-model="item.value"
                    ></a-input>
                    <a
                        @click="addSelect"
                        style="color: @primary-color; margin: 10px 0 0 0; font-size: 18px; display: inline-block"
                    >
                        <a-icon style="margin: 0 10px 0 0" theme="filled" type="plus-circle" />{{language.parameter_add_option}}
                    </a>
                </a-form-item>
                <a-form-item :label="language.parameter_label5">
                    <a-textarea
                        :placeholder="language.parameter_placeholder5"
                        :rows="4"
                        v-decorator="['description', { rules: [{ required: false, message: language.parameter_placeholder5 }] }]"
                    ></a-textarea>
                </a-form-item>
            </a-form>
        </a-modal>
    </div>
</template>

<script>
import { getParameterSetting, editParameterSetting } from '@/api/reconfig.js'
import storage from 'store'
export default {
    data() {
        return {
            parameterSettingModel: false,
            parameterSettingForm: this.$form.createForm(this, { name: 'parameterSettingForm' }),
            // 变量类型
            paramsType: 'string',
            // 字符串型参数
            string_parameter: [],
            // 选择型参数
            choice_parameter: [],
            // 可选项
            selectList: [
                {
                    value: '',
                },
            ],
            tableLoading: false,
            // 编辑或新增
            isadd: true,
            // 编辑的参数
            parameter: {},
            btnLoading: false,
        }
    },
    computed: {
        tableData() {
            this.string_parameter.map((item, index) => {
                item.paramsType = 'string'
                item.type_val = '字符串参数'
                item.code = index
                item.key = 'str' + index
            })
            this.choice_parameter.map((item, index) => {
                item.paramsType = 'select'
                item.type_val = '选项参数'
                item.code = index
                item.key = 'sel' + index
                item.default_string =
                    item.choices_string_list && item.choices_string_list instanceof Array
                        ? item.choices_string_list[0]
                        : item.choices_string_list
            })
            return this.string_parameter.concat(this.choice_parameter)
        },
        columns(){
            return [
                {
                    title: this.language.parameter_table1,
                    dataIndex: 'name',
                    key: 'name',
                    width: 150,
                },
                {
                    title: this.language.parameter_table2,
                    dataIndex: 'type_val',
                    key: 'type_val',
                    width: 150,
                },
                {
                    title: this.language.parameter_table3,
                    dataIndex: 'default_string',
                    key: 'default_string',
                    width: 150,
                },
                {
                    title: this.language.parameter_table4,
                    key: 'action',
                    scopedSlots: { customRender: 'action' },
                    width: 150,
                },
            ]
        }
    },
    created() {
        this.language = this.$store.state.language.languageAuth.pipelineConfiguration || {}
    },
    mounted() {
        this.getParameterSettingData()
    },
    methods: {
        // 删除
        deleted(record) {
            let _this = this
            this.$confirm({
                content: '确认要删除该变量吗？',
                okType: "danger",
                onOk() {
                    if (record.paramsType == 'string') {
                        _this.string_parameter.splice(record.code, 1)
                    } else if (record.paramsType == 'select') {
                        _this.choice_parameter.splice(record.code, 1)
                    }
                },
            })
        },
        // 提交后台
        onSunmit() {
            this.btnLoading = true
            let updata = {
                code: this.$route.query.appCode,
                job_name: this.$route.query.name,
                params: {
                    string_parameter: this.string_parameter,
                    choice_parameter: this.choice_parameter,
                },
                view_name:this.$route.query.view_name,
            }
            editParameterSetting(updata)
                .then((res) => {
                    if (res.code == 200) {
                        this.$message.success(res.message)
                        this.getParameterSettingData()
                    } else {
                        this.$message.error(res.message)
                    }
                })
                .finally(() => {
                    this.btnLoading = false
                })
        },
        // 弹框展开
        parameterSettingShow(record) {
            this.parameterSettingForm.resetFields()
            this.parameterSettingModel = true
            if (record) {
                this.isadd = false
                this.paramsType = record.paramsType
                this.parameter = record
                this.$nextTick(function () {
                    this.parameterSettingForm.setFieldsValue({
                        name: record.name,
                        paramsType: record.paramsType,
                        description: record.description,
                    })
                    if (record.paramsType == 'string') {
                        this.parameterSettingForm.setFieldsValue({
                            default_string: record.default_string,
                        })
                    } else {
                        this.selectList = []
                        record.choices_string_list.map((item) => {
                            this.selectList.push({
                                value: item,
                            })
                        })
                    }
                })
            } else {
                this.isadd = true
                this.paramsType = 'string'
                this.selectList = [{ value: '' }]
            }
        },
        // 类型切换
        typechange(val) {
            this.paramsType = val
        },
        // 添加选项
        addSelect() {
            if (this.selectList[this.selectList.length - 1].value != '') {
                this.selectList.push({ value: '' })
            } else {
                this.$message.warning('存在未填写的可选项')
            }
        },
        // 可选参数input框change
        inputchange() {
            this.selectList.map((item, index) => {
                if (item.value == '' && this.selectList.length > 1) {
                    this.selectList.splice(index, 1)
                }
            })
        },
        // 获取参数数据
        getParameterSettingData() {
            this.tableLoading = true
            getParameterSetting({ code: this.$route.query.appCode, job_name: this.$route.query.name, view_name:this.$route.query.view_name })
                .then((res) => {
                    if (res.code == 200 && res.data) {
                        this.string_parameter = res.data.string_parameter
                        this.choice_parameter = res.data.choice_parameter
                    }
                })
                .finally(() => [(this.tableLoading = false)])
        },
        // 添加(修改变量)
        handleOk() {
            this.parameterSettingForm.validateFields((error, values) => {
                if (!error) {
                    // 判断是否重复
                    if (this.isadd) {
                        let isreiterated = this.tableData.find((item) => {
                            return item.name == values.name
                        })

                        if (isreiterated) {
                            return this.$message.warning('该变量名已经存在,请更换')
                        }
                    }

                    if (this.paramsType == 'string') {
                        let obj = {
                            name: values.name,
                            description: values.description,
                            default_string: values.default_string,
                        }
                        if (this.isadd) {
                            this.string_parameter.push(obj)
                        } else {
                            this.$set(this.string_parameter, this.parameter.code, obj)
                        }

                        this.parameterSettingModel = false
                    } else if (this.paramsType == 'select') {
                        if (this.selectList.length == 1 && this.selectList[0].value == '') {
                            return this.$message.warning('请至少添加一个可选项')
                        }

                        let list = []
                        let flag
                        this.selectList.map((item, index) => {
                            if (item.value != '') {
                                list.push(item.value)
                            }
                        })
                        let list1 = list.slice().sort()
                        for (let i = 0; i < list1.length; i++) {
                            if (list1[i] == list1[i + 1]) {
                                flag = true
                            }
                        }
                        if (flag) {
                            return this.$message.warning('存在相同的可选项，请修改')
                        }

                        let obj = {
                            name: values.name,
                            description: values.description,
                            choices_string_list: list,
                        }
                        if (this.isadd) {
                            this.choice_parameter.push(obj)
                        } else {
                            this.$set(this.choice_parameter, this.parameter.code, obj)
                        }
                        this.parameterSettingModel = false
                    }
                }
            })
        },
    },
}
</script>

<style lang="less" scoped>
footer {
    height: 50px;
    button {
        float: right;
        margin: 20px 0 0 0;
    }
}
</style>