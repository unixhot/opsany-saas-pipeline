<template>
    <div class="step_modal_main">
        <!-- 新增or修改阶段 step -->
        <a-modal
            width="800px"
            :title="modalTitle"
            v-model="stepmodel"
            :destroyOnClose="true"
            @ok="stepHandleOk"
            @cancel="stepCancel"
        >
            <div class="stepmodalbody">
                <div class="left">
                    <a-tree
                        v-if="treeData.length > 0"
                        :tree-data="treeData"
                        :selectedKeys="selectedKey"
                        :defaultExpandAll="true"
                        @select="treeSelect"
                    />
                </div>
                <div class="right">
                    <a-form :label-col="{ span: 15 }" :wrapper-col="{ span: 24 }" :form="form1">
                        <!-- 最后完成阶段 post -->
                        <a-form-item v-if="islast" :label="language.step_label1">
                            <a-select
                                :placeholder="language.step_placeholder1"
                                v-decorator="[
                                    'posttype',
                                    { rules: [{ required: true, message: language.step_placeholder1 }] },
                                ]"
                            >
                                <a-select-option
                                    v-for="(item, index) in selectList"
                                    :key="index"
                                    :value="item.condition"
                                    >{{ item.ch_name }}</a-select-option
                                >
                            </a-select>
                        </a-form-item>
                        <!-- 打印 -->
                        <a-form-item :label="language.step_label2" v-if="toolName == 'echo'">
                            <a-textarea
                                :placeholder="language.step_placeholder2"
                                v-decorator="[
                                    'message',
                                    { rules: [{ required: true, message: language.step_placeholder2 }] },
                                ]"
                                :rows="4"
                            />
                        </a-form-item>
                        <!-- 脚本 -->
                        <a-form-item :label="language.step_label2" v-if="toolName == 'sh'">
                            <a-textarea
                                :placeholder="language.step_placeholder2"
                                v-decorator="[
                                    'script',
                                    { rules: [{ required: true, message: language.step_placeholder2 }] },
                                ]"
                                :rows="4"
                            />
                        </a-form-item>
                        <!-- git -->
                        <template v-else-if="toolName == 'git'">
                            <a-form-item :label="language.step_label3">
                                <a-input
                                    v-if="!gitErroe"
                                    @change="projectsChange"
                                    :placeholder="language.step_placeholder3"
                                    v-decorator="[
                                        'url',
                                        { rules: [{ required: true, message: language.step_placeholder3 }] },
                                    ]"
                                ></a-input>
                                <a-tooltip v-else>
                                    <template slot="title">
                                        {{ language.step_label3_message }}
                                        <!-- 代码仓库配置错误导致该功能无法使用，请前往工具管理进行配置 -->
                                    </template>
                                    <a-select
                                        :placeholder="language.step_placeholder3"
                                        disabled
                                        v-decorator="[
                                            'url',
                                            { rules: [{ required: true, message: language.step_placeholder3 }] },
                                        ]"
                                    ></a-select>
                                </a-tooltip>
                            </a-form-item>
                            <a-form-item :label="language.step_label5" :help="language.help">
                                <a-select
                                    :placeholder="language.step_placeholder5"
                                    v-decorator="[
                                        'credentialsId',
                                        { rules: [{ required: true, message: language.step_placeholder5 }] },
                                    ]"
                                    optionFilterProp="label"
                                    showSearch
                                >
                                    <a-select-option
                                        v-for="(item, index) in credentialsList"
                                        :key="index"
                                        :value="item.credentials_id"
                                        :label="item.name + item.credentials_id"
                                    >
                                        {{ item.name }}({{ item.credentials_id }} )
                                    </a-select-option>
                                </a-select>
                            </a-form-item>
                            <a-form-item :label="language.step_label4">
                                <a-input
                                    :placeholder="language.step_placeholder4"
                                    v-decorator="[
                                        'branch',
                                        {
                                            rules: [
                                                {
                                                    required: true,
                                                    message: language.step_placeholder4,
                                                    whitespace: true,
                                                },
                                            ],
                                            initialValue: 'master',
                                        },
                                    ]"
                                ></a-input>
                            </a-form-item>
                        </template>
                        <!-- 睡眠 -->
                        <template v-else-if="toolName == 'sleep'">
                            <a-form-item :label="language.step_label6">
                                <a-input-number
                                    :placeholder="language.step_placeholder6"
                                    style="width: 100%"
                                    v-decorator="[
                                        'time',
                                        { rules: [{ required: true, message: language.step_placeholder6 }] },
                                    ]"
                                    :min="1"
                                ></a-input-number>
                            </a-form-item>
                            <a-form-item :label="language.step_label7">
                                <a-select
                                    :placeholder="language.step_placeholder7"
                                    v-decorator="[
                                        'unit',
                                        { rules: [{ required: true, message: language.step_placeholder7 }] },
                                    ]"
                                >
                                    <a-select-option value="SECONDS">{{ language.SECONDS }}</a-select-option>
                                    <a-select-option value="MINUTES">{{ language.MINUTES }}</a-select-option>
                                    <a-select-option value="HOURS">{{ language.HOURS }}</a-select-option>
                                    <a-select-option value="DAYS">{{ language.DAYS }}</a-select-option>
                                </a-select>
                            </a-form-item>
                        </template>
                        <!-- 写文件 -->
                        <template v-else-if="toolName == 'writeFile'">
                            <a-form-item :label="language.step_label8">
                                <a-input
                                    :placeholder="language.step_placeholder8"
                                    v-decorator="[
                                        'file',
                                        { rules: [{ required: true, message: language.step_placeholder8 }] },
                                    ]"
                                ></a-input>
                            </a-form-item>
                            <a-form-item :label="language.step_label2">
                                <a-textarea
                                    :placeholder="language.step_placeholder2"
                                    v-decorator="[
                                        'text',
                                        { rules: [{ required: true, message: language.step_placeholder2 }] },
                                    ]"
                                    :rows="4"
                                />
                            </a-form-item>
                        </template>
                        <!-- 读文件 -->
                        <template v-else-if="toolName == 'readFile'">
                            <a-form-item :label="language.step_label8">
                                <a-input
                                    :placeholder="language.step_placeholder8"
                                    v-decorator="[
                                        'file',
                                        { rules: [{ required: true, message: language.step_placeholder8 }] },
                                    ]"
                                ></a-input>
                            </a-form-item>
                            <a-form-item :label="language.step_label9">
                                <a-input
                                    :placeholder="language.step_placeholder9"
                                    v-decorator="[
                                        'encoding',
                                        { rules: [{ required: false, message: language.step_placeholder9 }] },
                                    ]"
                                ></a-input>
                            </a-form-item>
                        </template>
                        <!-- 人工确认 -->
                        <template v-else-if="toolName == 'input'">
                            <a-form-item :label="language.step_label10">
                                <a-input
                                    :placeholder="language.step_placeholder10"
                                    v-decorator="[
                                        'message',
                                        { rules: [{ required: true, message: language.step_placeholder10 }] },
                                    ]"
                                ></a-input>
                            </a-form-item>
                        </template>
                    </a-form>
                </div>
            </div>
        </a-modal>
    </div>
</template>

<script>
import { getPipelineToolPost } from '@/api/pipeline-tool.js'
import { getCredentials } from '@/api/credential.js'
import { getProjects, getBranch } from '@/api/gitlab.js'
import storage from 'store'
export default {
    data() {
        return {
            // 新增or修改步骤(三级步骤)的弹框显示
            stepmodel: false,
            // 被选中的命令(tree)
            tool: {},
            // 被选中的命令的name
            toolName: '',
            form1: this.$form.createForm(this, { name: 'form1' }),
            // 是否是最后一列(结束阶段)
            islast: false,
            // 下拉菜单选项
            selectList: [],
            // 所修改的step
            activeStep: {},
            // tree选中项
            selectedKey: ['echo'],
            // 添加或编辑step
            isAdd: true,
            // 所编辑step所属post中的condition
            activeCondition: '',
            // 凭据选项
            credentialsList: [],
            // gitlab选项
            projectsList: [],
            // 分支选项
            branchList: [],
            // 标题
            modalTitle: '新增步骤',
            // 获取代码仓库出错(拉取代码不可用)
            gitErroe: false,
        }
    },
    props: ['treeData', 'pipelineData'],
    created() {
        this.language = this.$store.state.language.languageAuth.pipelineConfiguration || {}
    },
    mounted() {
        this.getPostData()
        // 获取凭据
        this.getCredentialsData()
        // 获取gitlab项目
        this.getProjectsData()
    },
    methods: {
        // 获取凭据
        getCredentialsData() {
            return getCredentials({
                search_type: 'typeName',
                search_data: 'SSH Username with private key',
                app_code: storage.get('__applicationInfo').code,
                all_data: 'true',
            }).then((res) => {
                if (res.code == 200 && res.data) {
                    this.credentialsList = res.data
                }
            })
        },
        // 获取gitlab项目
        getProjectsData() {
            getProjects()
                .then((res) => {
                    if (res.code == 200 && res.data) {
                        this.projectsList = res.data
                    } else {
                        this.gitErroe = true
                    }
                })
                .catch(() => {
                    this.gitErroe = true
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
            // this.getBranchData(option.key)
            // this.form1.resetFields("branch")
        },
        // 如果stageindex为-1表示操作的是结束阶段post
        // step存在表示是修改，不存在是添加
        show(stageindex, parallelindex, step, stepindex) {
            if (step) {
                this.modalTitle = '修改步骤'
                let _this = this
                console.log(parallelindex, step, stepindex)
                this.activeCondition = this.selectList[parallelindex]
                if (stageindex == -1) {
                    this.islast = true
                    this.stepindex = stepindex
                    _this.$nextTick(function () {
                        _this.form1.setFieldsValue({ posttype: _this.selectList[parallelindex].condition })
                    })
                } else {
                    this.islast = false
                }
                this.isAdd = false
                this.activeStep = step
                this.stepmodel = true
                this.toolName = step.name
                this.selectedKey = [step.name]
                this.treeData.map((item) => {
                    item.children.map((ele) => {
                        if (ele.name == step.name) {
                            this.tool = ele
                        }
                    })
                })
                if (step.name == 'git') {
                    let id = this.projectsList.find((item) => {
                        return item.ssh_url_to_repo == step.arguments[2].value.value
                    }).id
                    this.getBranchData(id)
                }
                this.$nextTick(function () {
                    step.arguments.map((item) => {
                        this.form1.setFieldsValue({ [item.key]: item.value.value })
                    })
                })
            } else {
                this.modalTitle = '新增步骤'
                this.isAdd = true
                this.selectedKey = ['echo']
                if (stageindex == -1) {
                    this.islast = true
                    this.$nextTick(function () {
                        this.form1.setFieldsValue({ posttype: 'always' })
                    })
                } else {
                    this.islast = false
                    this.operationStageIndex = stageindex
                    this.operationParallelindexIndex = parallelindex
                }
                this.stepmodel = true
                // 打开弹框默认选echo并在右侧文本框填入信息
                this.toolName = 'echo'
                this.treeData.map((item) => {
                    item.children.map((ele) => {
                        if (ele.name == 'echo') {
                            this.tool = ele
                        }
                    })
                })
                this.$nextTick(function () {
                    this.form1.setFieldsValue({ message: 'Hello OpsAny' })
                })
            }
        },
        // 步骤提交
        stepHandleOk() {
            this.form1.validateFields((err) => {
                let obj = JSON.parse(JSON.stringify({ name: this.tool.name, arguments: this.tool.arguments }))
                let name = this.tool.name
                if (name == 'echo' || name == 'sh') {
                    obj.arguments.map((item) => {
                        item.value.value = this.form1.getFieldValue(item.key)
                    })
                } else if (name == 'git') {
                    obj.arguments.map((item) => {
                        item.value.value = this.form1.getFieldValue(item.key)
                    })
                } else if (name == 'sleep') {
                    obj.arguments = [
                        {
                            key: 'time',
                            value: {
                                isLiteral: true,
                                value: this.form1.getFieldValue('time'),
                            },
                        },
                        {
                            key: 'unit',
                            value: {
                                isLiteral: true,
                                value: this.form1.getFieldValue('unit'),
                            },
                        },
                    ]
                } else if (name == 'writeFile') {
                    obj.arguments.map((item) => {
                        item.value.value = this.form1.getFieldValue(item.key)
                    })
                } else if (name == 'readFile') {
                    obj.arguments = [
                        {
                            key: 'file',
                            value: {
                                isLiteral: true,
                                value: this.form1.getFieldValue('file'),
                            },
                        },
                        {
                            key: 'encoding',
                            value: {
                                isLiteral: true,
                                value: this.form1.getFieldValue('encoding') || '',
                            },
                        },
                    ]
                } else if (name == 'input') {
                    obj.arguments = [
                        {
                            key: 'message',
                            value: {
                                isLiteral: true,
                                value: this.form1.getFieldValue('message'),
                            },
                        },
                    ]
                }

                if (this.isAdd) {
                    let steps
                    if (this.islast) {
                        let condition = this.pipelineData.pipeline.post.conditions.find((item) => {
                            return item.condition == this.form1.getFieldValue('posttype')
                        })
                        steps = condition.branch.steps
                    } else {
                        let state = this.pipelineData.pipeline.stages[this.operationStageIndex]
                        let parallel = state.parallel[this.operationParallelindexIndex]
                        // console.log(parallel)
                        steps = parallel.branches[0].steps
                    }

                    steps.push(obj)
                    this.stepmodel = false
                } else {
                    // console.log(obj)
                    this.activeStep.name = obj.name
                    this.activeStep.arguments = JSON.parse(JSON.stringify(obj.arguments))
                    this.activeStep.arguments.map((item) => {
                        item.value.value = this.form1.getFieldValue(item.key) || ''
                    })
                    this.stepmodel = false
                    if (this.islast) {
                        if (this.form1.getFieldValue('posttype') != this.activeCondition.condition) {
                            let condition = this.pipelineData.pipeline.post.conditions.find((item) => {
                                return item.condition == this.activeCondition.condition
                            })
                            let steps = condition.branch.steps
                            console.log(this.stepindex)
                            steps.splice(this.stepindex, 1)

                            let condition1 = this.pipelineData.pipeline.post.conditions.find((item) => {
                                return item.condition == this.form1.getFieldValue('posttype')
                            })
                            var steps1 = condition1.branch.steps
                            steps1.push(obj)
                        }
                    }
                }
                // console.log(this.activeStep)
            })
        },
        // 步骤取消
        stepCancel() {
            this.stepmodel = false
        },
        // 树选择
        treeSelect(selectkey, e) {
            let _this = this
            this.tool = e.node.dataRef
            let toolname = this.tool.name
            this.toolName = toolname
            this.selectedKey = selectkey
            // console.log(selectkey,toolname, e)
            this.$nextTick(function () {
                // 因echo和input的输入框v-decorator都是message，不加settimeout会报错
                setTimeout(function () {
                    if (toolname == 'echo' || toolname == 'sh') {
                        _this.tool.arguments.map((item) => {
                            let key = item.key
                            _this.form1.setFieldsValue({ [key]: item.value.value })
                        })
                    } else if (toolname == 'git') {
                        // _this.tool.arguments.map(item => {
                        //     let key = item.key
                        //     _this.form1.setFieldsValue({ [key]: item.value.value })
                        // })
                    } else if (toolname == 'sleep') {
                        _this.form1.setFieldsValue({ time: 5, unit: 'SECONDS' })
                    } else if (toolname == 'writeFile') {
                        _this.tool.arguments.map((item) => {
                            let key = item.key
                            _this.form1.setFieldsValue({ [key]: item.value.value })
                        })
                    } else if (toolname == 'readFile') {
                        _this.form1.setFieldsValue({ file: 'README.md' })
                    } else if (toolname == 'input') {
                        _this.form1.setFieldsValue({ message: '是否继续执行构建' })
                    }
                }, 10)
            })
            // console.log(this.tool)
        },
        // 获取post的执行条件数据(success等)
        getPostData() {
            getPipelineToolPost().then((res) => {
                if (res.code == 200 && res.data) {
                    this.selectList = res.data
                }
            })
        },
    },
}
</script>

<style lang="less" scoped>
/deep/.ant-modal-content {
    .ant-modal-body {
        padding: 0;
    }
}

/deep/.stepmodalbody {
    display: flex;
    .left {
        border-right: 1px solid #ddd;
        width: 180px;
        .ant-tree-treenode-disabled {
            //一级菜单
            border-bottom: 1px solid #ddd;
            background: #f5f7fa;
            padding: 0;
            .ant-tree-switcher {
                // 前面的图标
                margin: 5px 0 0 0;
            }
            .ant-tree-node-content-wrapper {
                // 一级菜单名称
                margin: 5px 0;
            }
            .ant-tree-child-tree {
                background: #fff;
                padding: 0;
                .ant-tree-treenode-switcher-open {
                    border-top: 1px solid #ddd;
                    padding: 0px 0;
                    .ant-tree-node-selected {
                        background: #fff;
                        color: #198eff;
                    }
                }
            }
        }
    }
    .right {
        padding: 40px 30px;
        width: 620px;

        .ant-form-item-label {
            text-align: left;
        }
    }
}
</style>
