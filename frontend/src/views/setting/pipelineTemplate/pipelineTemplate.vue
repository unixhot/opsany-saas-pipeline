<template>
    <!-- pipelineTemplate 流水线模板 -->

    <div class="pipelineTemplate_main">
        <a-spin :spinning="loading">
            <content-header>
                <div slot="docs">
                    {{ language.tip }}
                    <a
                        class="more"
                        style="margin-left: 5px; margin-top: 10px; font-size: 14px; color: @primary-color"
                        href="/docs/user-guide/devops/#_8"
                        target="_blank"
                    >
                        {{ language.more }}
                        <a-icon type="file-text" />
                    </a>
                </div>
            </content-header>
            <div v-if="noJenkins" style="background: #fff">
                <a-empty
                    image="https://gw.alipayobjects.com/mdn/miniapp_social/afts/img/A*pevERLJC9v0AAAAAAAAAAABjAQAAAQ/original"
                    :image-style="{ height: '80px' }"
                    style="padding: 280px 0 280px 0"
                >
                    <p style="margin: 20px 0 0 0" slot="description">
                        {{ language.noJenkins1
                        }}<a style="color: #076aff" @click="$router.push({ path: '/setting/systemSettings' })">{{
                            language.noJenkins2
                        }}</a
                        >{{ language.noJenkins3 }}
                    </p>
                </a-empty>
            </div>
            <a-card v-else>
                <div class="top">
                    <a-radio-group
                        style="margin: 0 0 20px 0"
                        @change="typeChange"
                        v-model="deployType"
                        button-style="solid"
                    >
                        <a-radio-button value="inner"> {{ language.radioList1 }} </a-radio-button>
                        <a-radio-button value="outer"> {{ language.radioList2 }} </a-radio-button>
                    </a-radio-group>
                    <div>
                        <a-button
                            v-if="
                                deployType == 'inner' &&
                                $store.state.btnAuth.btnAuth.pipeline_job_built_in_template_folder_create
                            "
                            icon="plus"
                            @click="addGroupShow"
                            >{{ language.addGroup }}</a-button
                        >
                        <a-button
                            v-if="
                                deployType == 'outer' &&
                                $store.state.btnAuth.btnAuth.pipeline_job_template_folder_create
                            "
                            icon="plus"
                            @click="addGroupShow"
                            >{{ language.addGroup }}</a-button
                        >
                        <a-button
                            v-if="
                                deployType == 'inner' &&
                                $store.state.btnAuth.btnAuth.pipeline_job_built_in_template_create
                            "
                            icon="plus"
                            style="margin: 0 0 0 10px"
                            @click="addTemplate(null)"
                            type="primary"
                            >{{ language.addTemplate }}</a-button
                        >
                        <a-button
                            v-if="deployType == 'outer' && $store.state.btnAuth.btnAuth.pipeline_job_template_create"
                            icon="plus"
                            style="margin: 0 0 0 10px"
                            @click="addTemplate(null)"
                            type="primary"
                            >{{ language.addTemplate }}</a-button
                        >
                    </div>
                </div>
                <a-collapse :activeKey="index == 0 ? 1 : ''" v-for="(item, index) in groupData" :key="item.code">
                    <a-collapse-panel key="1" :header="item.name">
                        <div v-if="deployType == 'inner'" class="operate" slot="extra">
                            <a v-if="$store.state.btnAuth.btnAuth.pipeline_job_built_in_template_create" style="margin: 0 10px 0 0" @click="addTemplate(item.code)">{{ language.addTemplate }}</a>
                            <a v-if="$store.state.btnAuth.btnAuth.pipeline_job_built_in_template_folder_update" @click.stop="editGroup(item)" style="margin: 0 10px 0 0">{{ language.edit }}</a>
                            <a v-if="$store.state.btnAuth.btnAuth.pipeline_job_built_in_template_folder_delete" @click.stop="deleteGroup(item)">{{ language.delete }}</a>
                        </div>
                        <div v-if="deployType == 'outer'" class="operate" slot="extra">
                            <a v-if="$store.state.btnAuth.btnAuth.pipeline_job_template_create" style="margin: 0 10px 0 0" @click="addTemplate(item.code)">{{ language.addTemplate }}</a>
                            <a v-if="$store.state.btnAuth.btnAuth.pipeline_job_template_folder_update" @click.stop="editGroup(item)" style="margin: 0 10px 0 0">{{ language.edit }}</a>
                            <a v-if="$store.state.btnAuth.btnAuth.pipeline_job_template_folder_delete" @click.stop="deleteGroup(item)" >{{ language.delete }}</a>
                        </div>
                        <div
                            class="template_list"
                            v-if="item.pipeline_template_list && item.pipeline_template_list.length > 0"
                        >
                            <div class="template_cell" v-for="ele in item.pipeline_template_list" :key="ele.code">
                                <h5 :title="ele.name">{{ ele.name }}</h5>
                                <p :title="ele.description">{{ ele.description || '--' }}</p>
                                <a-dropdown>
                                    <a class="ant-dropdown-link" @click="(e) => e.preventDefault()">
                                        <a-icon style="font-size: 18px" type="more" />
                                    </a>
                                    <a-menu v-if="deployType == 'inner'" slot="overlay">
                                        <a-menu-item
                                            v-if="$store.state.btnAuth.btnAuth.pipeline_job_built_in_template_update"
                                            @click="editTemplate(ele)"
                                        >
                                            {{ language.edit }}
                                        </a-menu-item>
                                        <a-menu-item
                                            v-if="$store.state.btnAuth.btnAuth.pipeline_job_built_in_template_copy"
                                            @click="copyTemplate(ele)"
                                        >
                                            {{ language.copy }}
                                        </a-menu-item>
                                        <a-menu-item
                                            v-if="$store.state.btnAuth.btnAuth.pipeline_job_built_in_template_delete"
                                            @click="deleteTemplate(ele)"
                                        >
                                            {{ language.delete }}
                                        </a-menu-item>
                                    </a-menu>
                                    <a-menu v-if="deployType == 'outer'" slot="overlay">
                                        <a-menu-item
                                            v-if="$store.state.btnAuth.btnAuth.pipeline_job_template_update"
                                            @click="editTemplate(ele)"
                                        >
                                            {{ language.edit }}
                                        </a-menu-item>
                                        <a-menu-item
                                            v-if="$store.state.btnAuth.btnAuth.pipeline_job_template_update"
                                            @click="copyTemplate(ele)"
                                        >
                                            {{ language.copy }}
                                        </a-menu-item>
                                        <a-menu-item
                                            v-if="$store.state.btnAuth.btnAuth.pipeline_job_template_delete"
                                            @click="deleteTemplate(ele)"
                                        >
                                            {{ language.delete }}
                                        </a-menu-item>
                                    </a-menu>
                                </a-dropdown>
                            </div>
                        </div>
                        <div v-else style="text-align: center">
                            <a-empty :description="false"></a-empty>
                            {{ language.no_data }}
                            <span
                                v-if="
                                    deployType == 'inner' &&
                                    $store.state.btnAuth.btnAuth.pipeline_job_built_in_template_create
                                "
                                >，<a @click="addTemplate(item.code)">{{ language.creatTemplate }}</a></span
                            >
                            <span
                                v-if="
                                    deployType == 'outer' && $store.state.btnAuth.btnAuth.pipeline_job_template_create
                                "
                                >，<a @click="addTemplate(item.code)">{{ language.creatTemplate }}</a></span
                            >
                        </div>
                    </a-collapse-panel>
                </a-collapse>
                <div style="margin:80px 0" v-if="groupData.length == 0">
                    <a-empty>
                        <template #description>
                            <p>暂无数据 ，请新建分组后自定义流水线模板</p>
                        </template>
                    </a-empty>
                </div>
            </a-card>
        </a-spin>
        <Group @father="getTemplateGroupData(), getGroupList()" ref="Group"></Group>
        <a-modal :confirmLoading="btnLoading" :title="language.title" v-model="copyModel" @ok="copyHandle">
            <a-form :form="copyForm" :label-col="{ span: 5 }" :wrapper-col="{ span: 17 }">
                <a-form-item :label="language.label1">
                    <a-input
                        :placeholder="language.placeholder1"
                        v-decorator="['name', { rules: [{ required: true, message: language.placeholder1 }] }]"
                    ></a-input>
                </a-form-item>
                <a-form-item :label="language.label2">
                    <a-select
                        :placeholder="language.placeholder2"
                        v-decorator="['group_id', { rules: [{ required: true, message: language.placeholder2 }] }]"
                        optionFilterProp="label"
                        showSearch
                    >
                        <a-select-option
                            v-for="(item, index) in groupList"
                            :value="item.code"
                            :key="index"
                            :label="item.name"
                        >
                            <span v-if="item.built_in">({{ language.inner }})</span> {{ item.name }}
                        </a-select-option>
                    </a-select>
                </a-form-item>
                <a-form-item :label="language.label3">
                    <a-textarea
                        :placeholder="language.placeholder3"
                        :rows="6"
                        v-decorator="['description', { rules: [{ max: 100, message: language.placeholder3 }] }]"
                    ></a-textarea>
                </a-form-item>
            </a-form>
        </a-modal>
    </div>
</template>

<script>
import Group from './model/group.vue'
import {
    getPipelineTemplateGroup,
    deletePipelineTemplateGroup,
    copyTemplate,
    deleteTemplate,
} from '@/api/pipelineTemplate.js'

export default {
    data() {
        return {
            // 样式
            customStyle: 'background: #f7f7f7;margin-bottom: 24px;border:none;overflow: hidden',
            columns: [
                {
                    title: '模板名称',
                    dataIndex: 'name',
                    key: 'name',
                },
                {
                    title: '类别',
                    dataIndex: 'type',
                    key: 'type',
                },
                {
                    title: '流程',
                    dataIndex: 'stage_list',
                    key: 'stage_list',
                    width: 500,
                    scopedSlots: { customRender: 'stage_list' },
                },
                {
                    title: '描述',
                    key: 'description',
                    dataIndex: 'description',
                    width: '30%',
                    ellipsis: true,
                },
                {
                    title: '操作',
                    key: 'action',
                    scopedSlots: { customRender: 'action' },
                },
            ],
            // 分组
            groupData: [],
            // 复制模板弹框
            copyModel: false,
            copyForm: this.$form.createForm(this, { name: 'copyForm' }),
            btnLoading: false,
            noJenkins: false,
            loading: true,
            deployType: 'inner',
            // 分组数据
            groupList: [],
            // 全部分组
            allGroupList: [],
            // 内置分组
            innergroupList: [],
            // 自定义分组
            outergroupList: [],
        }
    },
    created() {
        this.language = this.$store.state.language.languageAuth.pipelineTemplate || {}
    },
    mounted() {
        this.getTemplateGroupData()
        this.getGroupList()
    },
    methods: {
        // 新增模板
        addTemplate(groupCode) {
            if (this.deployType == 'inner') {
                window.sessionStorage.setItem('is_inner_pipeline', true)
            } else {
                window.sessionStorage.setItem('is_inner_pipeline', false)
            }
            this.$router.push({ path: '/setting/pipelineTemplate/setPipelineTemplate', query:{ groupCode:groupCode}})
        },
        // 编辑模板
        editTemplate(record) {
            if (this.deployType == 'inner') {
                window.sessionStorage.setItem('is_inner_pipeline', true)
            } else {
                window.sessionStorage.setItem('is_inner_pipeline', false)
            }
            this.$router.push({ path: '/setting/pipelineTemplate/setPipelineTemplate', query: { code: record.code } })
        },
        // 切换内置和自定义
        typeChange(val) {
            if (val.target.value == 'inner') {
                this.groupData = this.innergroupList
                this.groupList = this.allGroupList
            } else {
                this.groupData = this.outergroupList
                this.groupList = this.outergroupList
            }
        },
        addGroupShow() {
            this.$refs.Group.show(false, this.deployType)
        },
        // 获取流水线模板分组
        getTemplateGroupData() {
            this.loading = true
            getPipelineTemplateGroup()
                .then((res) => {
                    this.groupData = []
                    if (res.code == 200 && res.data) {
                        this.allGroupList = res.data
                        this.innergroupList = res.data.filter((item) => {
                            return item.built_in
                        })
                        this.outergroupList = res.data.filter((item) => {
                            return !item.built_in
                        })
                        if (this.deployType == 'inner') {
                            this.groupData = this.innergroupList
                        } else {
                            this.groupData = this.outergroupList
                        }
                    }
                })
                .catch((res) => {
                    if (res.code == 404 && res.errcode == 40401) {
                        this.noJenkins = true
                    }
                })
                .finally(() => {
                    this.loading = false
                })
        },
        editGroup(record) {
            this.$refs.Group.show(record)
        },
        // 删除分组
        deleteGroup(record) {
            let _this = this
            this.$confirm({
                content: '确认删除该分组吗？',
                okType: 'danger',
                onOk() {
                    deletePipelineTemplateGroup({ code: record.code }).then((res) => {
                        if (res.code == 200) {
                            _this.$message.success(res.message)
                            _this.getTemplateGroupData()
                            _this.getGroupList()
                        } else {
                            _this.$message.error(res.message)
                        }
                    })
                },
            })
        },
        // 复制
        copyTemplate(record) {
            this.templateCode = record.code
            this.copyForm.resetFields()
            this.copyModel = true
            this.$nextTick(function () {
                this.copyForm.setFieldsValue({
                    name: record.name + ' (复制)',
                    group_id: this.groupList[0].code,
                    description: record.description,
                })
            })
        },
        // 获取分组选项(新建时选择所属分组时使用)
        getGroupList() {
            getPipelineTemplateGroup({ group: true }).then((res) => {
                if (res.code == 200 && res.data) {
                    this.groupList = res.data
                }
            })
        },
        // 复制模板提交
        copyHandle() {
            this.copyForm.validateFields((err, values) => {
                if (!err) {
                    let built_in
                    let group = this.groupList.find((item) => {
                        return item.code == values.group_id
                    })
                    if (group) {
                        built_in = group.built_in
                    }
                    this.btnLoading = true
                    copyTemplate({ ...values, template_id: this.templateCode, built_in: built_in })
                        .then((res) => {
                            if (res.code == 200) {
                                this.$message.success(res.message)
                                this.copyModel = false
                                this.getTemplateGroupData()
                            } else {
                                this.$message.warning(res.message)
                            }
                        })
                        .finally(() => {
                            this.btnLoading = false
                        })
                }
            })
        },
        // 删除模板
        deleteTemplate(record) {
            let _this = this
            this.$confirm({
                content: '确认要删除该流水线模板吗？',
                okType: 'danger',
                onOk() {
                    return deleteTemplate({ code: record.code }).then((res) => {
                        if (res.code == 200) {
                            _this.$message.success(res.message)
                            _this.getTemplateGroupData()
                        } else {
                            _this.$message.warning(res.message)
                        }
                    })
                },
            })
        },
    },
    components: {
        Group,
    },
}
</script>

<style lang="less" scoped>
.top {
    display: flex;
    justify-content: space-between;
}
.template_list {
    .template_cell {
        display: inline-block;
        width: calc(33.3% - 20px);
        // border: 1px solid #e8e8e8;
        box-shadow: 0 0 8px 2px #e8e8e8;
        margin: 10px;
        height: 80px;
        padding: 12px 120px 10px 20px;
        float: left;
        position: relative;
        h5 {
            font-size: 16px;
            font-weight: 1000;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            width: 100%;
        }
        p {
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            width: 100%;
        }
        .ant-dropdown-link {
            position: absolute;
            top: 30px;
            right: 20px;
            i {
                color: #333;
            }
            i:hover {
                color: @primary-color;
            }
        }
        .copy {
            position: absolute;
            top: 20px;
            right: 20px;
        }
    }
}

/deep/.ant-collapse-content {
    border: none;
}
/deep/.ant-radio-button-wrapper {
    // width: 120px;
    text-align: center;
}
.ant-collapse > .ant-collapse-item {
    border: none;
}
.ant-collapse {
    border: none;
    margin: 0 0 20px 0;
}
.operate {
    font-size: 14px;
    // display: none;
    i:hover {
        color: @primary-color;
    }
}
.ant-collapse-header {
    &:hover {
        .operate {
            display: block;
        }
    }
}
</style>