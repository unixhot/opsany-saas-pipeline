<template>
    <div>
        <!-- AddAssemblyLine 新建流水线 -->
        <a-drawer
            width="1000px"
            :bodyStyle="{ paddingBottom: '80px', paddingRight: '44px',}"
            :visible="addAssemblyLineModel"
            title="新建流水线"
            @close="onClose"
        >
            <a-steps style="width: 500px; margin: 0 auto 70px" :current="current">
                <a-step v-for="item in steps" :key="item.title" :title="item.title" />
            </a-steps>
            <a-form v-show="current == 0" :form="assemblyLineForm" :label-col="{ span: 3 }" :wrapper-col="{ span: 21 }">
                <a-spin :spinning="spinning" tip="正在加载中，请耐心等待...">
                <a-form-item label="流水线名称">
                    <a-input
                        placeholder="请输入流水线名称,仅支持数字、字母、下划线、中划线。"
                        v-decorator="[
                            'name',
                            {
                                rules: [
                                    {
                                        required: true,
                                        pattern: /^[0-9a-zA-Z-_]{1,}$/,
                                        message: '请输入流水线名称，仅支持仅支持数字、字母、下划线、中划线。',
                                    },
                                    {
                                        max: 50,
                                        message: '流水线名称长度限制在50个字符以内。',
                                    }
                                ],
                            },
                        ]"
                    />
                </a-form-item>
                <a-form-item label="所属应用">
                    <a-tree-select
                        dropdownClassName="resource-tree-select-addAssemblyLine"
                        treeNodeFilterProp="title"
                        v-decorator="['code', { rules: [{ required: true, message: '请选择所属应用' }] }]"
                        showSearch
                        :treeData="treeData"
                        style="width: 85%"
                        placeholder="请选择所属应用"
                        tree-default-expand-all
                        @change="treeChange"
                    >
                    </a-tree-select>
                    <span style="position: absolute; right: -120px">
                        <a-button icon="redo" style="margin:0 10px 0 0;" class="background_color" :loading="btnLoading2" @click="getBusinessTreeData">
                        </a-button>
                        <a
                            target="_blank"
                            :href="otherAppUrl + 'devops/#/configure/application'"
                            >创建应用 ></a
                        >
                    </span>
                </a-form-item>
                <a-form-item label="流水线描述">
                    <a-textarea
                        placeholder="描述长度限制在一百字内"
                        :auto-size="{ minRows: 4, maxRows: 6 }"
                        v-decorator="[
                            'description',
                            { rules: [{ required: false, max: 100, message: '长度不能超过100字' }] },
                        ]"
                    />
                </a-form-item>
                <a style="margin-left:12.5%;" @click="isShow = !isShow"> {{isShow?"关闭高级选项":"打开高级选项"}} </a>
                <div v-if="isShow" style="margin:20px 0 0 0;">
                    <a-form-item label="关联全局视图" help="全局视图可以跨应用对流水线进行分组管理。">
                        <a-select allowClear placeholder="选择所关联的全局视图" 
                        v-decorator="[
                            'overall_view_code',
                        ]">
                            <a-select-option v-for="item in viewList" :key="item.code">{{item.overall_view_name}}</a-select-option>
                        </a-select>
                    </a-form-item>
                    <a-form-item style="margin:20px 0 0 0;" label="关联应用视图" help="应用视图可以在应用内对流水线进行分组管理。">
                        <a-select allowClear placeholder="选择所关联的应用视图" 
                        v-decorator="[
                            'pipeline_group_code',
                        ]">
                            <a-select-option v-for="item in viewGroupList" :key="item.code">{{item.name}}</a-select-option>
                        </a-select>
                    </a-form-item>
                </div>
                </a-spin>
            </a-form>
            <div v-show="current == 1">
                <div class="template_main">
                    <div class="left">
                        <!-- <a-tree :tree-data="treeData" /> -->
                        <p
                            @click="groupSelect(item)"
                            :title="item.name"
                            :class="{ group: true, activeGroup: activeGroupIndex == item.code ? true : false }"
                            v-for="item in groupList"
                            :key="item.code"
                        >
                            {{ item.name }}
                        </p>
                    </div>
                    <div class="right">
                        <div class="templates">
                            <div
                                @click="templateChange(ele)"
                                v-for="ele in templateList"
                                :key="ele.code"
                                :class="{ template: true, activeTemplate: activeTemplateIndex == ele.code }"
                            >
                                <h3>{{ ele.name }}</h3>
                                <p>{{ ele.description || '--' }}</p>
                                <div class="big_ring"></div>
                                <div class="small_round"></div>
                            </div>
                        </div>
                        <a-empty
                            v-if="templateList && templateList.length == 0"
                            description="当前分组下暂无可用模板~"
                            style="margin: 100px 0 0 0"
                        ></a-empty>
                    </div>
                </div>
            </div>

            <div class="footerbtn">
                <a-checkbox v-if="current == 1" :checked="checked" @change="checkboxChange"> 前往配置详情 </a-checkbox>
                <a-button style="margin: 0 30px 0 0" @click="assemblyLineCancel">{{
                    current == '0' ? '取消' : '上一步'
                }}</a-button>
                <a-button :loading="btnLoading" @click="assemblyLineHandleOk" type="primary">{{
                    current == '0' ? '下一步' : '提交'
                }}</a-button>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import storage from 'store'
import { getPipelineTemplateGroup } from '@/api/pipelineTemplate.js'
import { addAssemblyLine, getPipelineView, getPipelineGroup } from '@/api/assemblyLine'
import { getBusinessTree } from '@/api/business.js'
export default {
    data() {
        return {
            // 抽屉是否显示
            addAssemblyLineModel: false,
            // 新建流水线确定按钮
            btnLoading: false,
            current: 0,
            // 选中的模板，未选择为-1
            activeTemplateIndex: -1,
            treeData: [],
            assemblyLineForm: this.$form.createForm(this, { name: 'assemblyLineForm' }),
            steps: [
                {
                    title: '基本信息',
                    // content: 'First-content',
                },
                {
                    title: '选择模板',
                    // content: 'Second-content',
                },
            ],
            // 选中的模板组
            activeGroupIndex: -1,
            // 模板组数据
            groupList: [],
            // 模板数据
            templateList: [],
            // 是否跳转流水线配置
            checked: true,
            // 提交模板数据
            config_xml: '',
            otherAppUrl: window.API_ROOT.replace('/pipeline', ''),
            // 选中的应用名称
            selectApplication:"",
            btnLoading2: false,
            spinning: true,
            appCode: 0,

            isShow: false,
            viewList: [],
            viewGroupList: [],
            selectApplicationCode:"",
        }
    },
    mounted() {
        
    },
    methods: {
        // 获取流水线分组
        getPipelineGroupData() {
            getPipelineGroup({ app_code:this.selectApplicationCode }).then(res=>{
                this.viewGroupList = res.data
            })
        },
        // 获取流水线视图
        getPipelineViewData() {
            getPipelineView().then(res=>{
                this.viewList = res.data
            })
        },
        // 获取业务与应用
        getBusinessTreeData(first) {
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
                            if(first && this.appCode && this.appCode == ele.code) {
                                this.selectApplication = ele.unique_code
                                this.selectApplicationCode = ele.code
                                this.getPipelineGroupData()
                            }
                        })
                    })
                }
            }).finally(()=>{
                this.btnLoading2 = false
                this.spinning = false
            })
        },
        // 初始化
        initialization() {
            this.assemblyLineForm.resetFields()
            this.activeGroupIndex = this.groupList.find((item) => item.name == '默认分组').code
            this.templateList = this.groupList.find((item) => item.name == '默认分组').pipeline_template_list
            this.activeTemplateIndex = this.templateList.find((item) => item.name == '使用通用模板').code
            this.config_xml = this.templateList.find((item) => item.name == '使用通用模板').template
            this.selectApplication = ""
            this.selectApplicationCode = ""
            this.appCode = 0
            this.current = 0
            this.checked = true
            this.viewList = []
            this.viewGroupList = []
            this.isShow = false
        },
        // 抽屉展示
        show(appCode,params) {
            this.params = params
            this.spinning = true
            if (appCode) {
                this.appCode = appCode
                setTimeout(()=>{
                    this.assemblyLineForm.setFieldsValue({ code: appCode })
                },10)
            }
            this.addAssemblyLineModel = true
            this.getPipelineTemplateGroup()
            this.getBusinessTreeData(true)
            this.getPipelineViewData()
        },
        // 选择模板组
        groupSelect(record) {
            this.activeGroupIndex = record.code
            this.templateList = record.pipeline_template_list
        },
        // 选择模板
        templateChange(record) {
            this.activeTemplateIndex = record.code
            this.config_xml = record.template
        },
        checkboxChange(e) {
            this.checked = e.target.checked
        },
        // 获取模板及模板组数据
        getPipelineTemplateGroup() {
            getPipelineTemplateGroup().then((res) => {
                if (res.code == 200 && res.data) {
                    this.groupList = res.data
                    this.activeGroupIndex = this.groupList.find((item) => item.name == '默认分组').code
                    this.templateList = this.groupList.find((item) => item.name == '默认分组').pipeline_template_list
                    this.activeTemplateIndex = this.templateList.find((item) => item.name == '使用通用模板').code
                    this.config_xml = this.templateList.find((item) => item.name == '使用通用模板').template
                    
                }
            })
        },
        // 抽屉右上角关闭
        onClose() {
            this.addAssemblyLineModel = false
            this.initialization()
        },
        treeChange(value,select,extra){
            this.selectApplication = extra?.triggerNode?.dataRef?.unique_code
            this.selectApplicationCode = extra?.triggerNode?.dataRef?.code
            this.getPipelineGroupData()
        },
        // 新增流水线提交
        assemblyLineHandleOk() {
            if (this.current == 0) {
                this.assemblyLineForm.validateFields((err, val) => {
                    if (!err) {
                        this.current++
                        this.values = val
                    }
                })
            } else {
                if (this.activeTemplateIndex > -1) {
                    this.btnLoading = true
                    let params = { ...this.values, config_xml: this.config_xml }
                    params.name = this.selectApplication + "-" + params.name
                    addAssemblyLine(params)
                        .then((res) => {
                            if (res.code == 200) {
                                this.$message.success(res.message)
                                this.addAssemblyLineModel = false
                                if (this.checked) {
                                    this.$router.push({
                                        path: '/applicationDelivery/assemblyLine/pipelineConfiguration',
                                        query: { name: params.name, appCode: this.values.code, ...this.params, },
                                    })
                                }
                                this.initialization()
                                this.$emit('father')
                            } else {
                                this.$message.error(res.message)
                            }
                        })
                        .finally(() => {
                            this.btnLoading = false
                        })
                } else {
                    this.$message.warning('请选择一个模板')
                }
            }
        },
        // 流水线弹框取消
        assemblyLineCancel() {
            if (this.current == 0) {
                this.addAssemblyLineModel = false
                this.initialization()
            } else {
                this.current--
            }
        },
    },
}
</script>

<style scoped lang="less">
.template_main {
    display: flex;
    margin: 10px 0 0 0;
    .left {
        margin: 0 30px 0 0;
        .group {
            font-size: 14px;
            height: 54px;
            line-height: 54px;
            width: 150px;
            border-right: 1px solid #eee;
            margin: 0;
            padding: 0 20px 0 0;
            text-align: right;
            cursor: pointer;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }
        .activeGroup {
            border-right: 2px solid @primary-color;
            color: @primary-color;
            padding: 0 19px 0 0;
            font-weight: 1000;
        }
    }
    .right {
        flex: 0px 1 1;
    }
    .templates {
        .template {
            height: 88px;
            border-radius: 5px;
            padding: 5px 10px;
            cursor: pointer;
            width: 550px;
            margin: 0 0 20px 0;
            box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.137254901960784);
            border: 1px solid #fff;
            position: relative;
            &:hover {
                border: 1px solid #ccc;
                .big_ring {
                    display: block;
                }
            }
            h3 {
                font-size: 16px;
                font-weight: 1000;
            }
            p {
                font-size: 12px;
            }
            .big_ring {
                border: 1px solid #eee;
                height: 20px;
                width: 20px;
                border-radius: 50%;
                position: absolute;
                right: 10px;
                top: 30px;
                border: 1px solid #cccccc;
                display: none;
            }
        }
        .activeTemplate {
            border: 1px solid @primary-color !important;
            .big_ring {
                display: block !important;
                border: 1px solid @primary-color;
            }
            .small_round {
                position: absolute;
                width: 10px;
                height: 10px;
                background: @primary-color;
                top: 35px;
                right: 15px;
                border-radius: 50%;
            }
        }
    }
}
.footerbtn {
    position: absolute;
    bottom: 0px;
    left: 0px;
    padding:10px 10px 10px 350px;
    z-index: 99;
    background: #fff;
    width:100%;
    border-top:1px solid #e8e8e8;
}
.background_color{
    position: relative;
    border: none;
    color: @primary-color;
    &:before {
        content: "";
        width:32px;
        height:32px;
        background: @primary-color;
        display: block;
        opacity: 0.1;
        position: absolute;
        top:0;
        z-index:0;
    }
}
</style>


<style lang="less">
.resource-tree-select-addAssemblyLine {
    max-height: 400px !important;
}
</style>

<style>
.resource-tree-select-addAssemblyLine .ant-select-tree-switcher {
	position: relative;
}
.resource-tree-select-addAssemblyLine .ant-select-tree-switcher_open::before,
.resource-tree-select-addAssemblyLine .ant-select-tree-switcher_close::before {
	content: "";
	position: absolute;
	right: -360px;
	top: 0;
	left: 0;
	bottom: 0;
}
</style>