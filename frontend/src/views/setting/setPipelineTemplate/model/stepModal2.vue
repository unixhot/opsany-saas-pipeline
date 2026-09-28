<template>
    <div class="step_modal_main">
        <!-- 新增or修改阶段 step -->
        <a-modal
            width="620px"
            :title="modalTitle"
            v-model="stepmodel"
            :destroyOnClose="true"
            @ok="stepHandleOk"
            @cancel="stepCancel"
        >
            <div class="stepmodalbody">
                <div class="right">
                    <a-form :label-col="{ span: 15 }" :wrapper-col="{ span: 24 }" :form="form1">
                        <!-- 最后完成阶段 post -->
                        <a-form-item v-if="islast" label="执行条件">
                            <a-select
                                v-decorator="['posttype', { rules: [{ required: true, message: '请输入代码仓库' }] }]"
                                optionFilterProp="label"
                                showSearch
                            >
                                <a-select-option
                                    v-for="(item, index) in selectList"
                                    :key="index"
                                    :value="item.condition"
                                    :label="item.ch_name"
                                    >{{ item.ch_name }}</a-select-option
                                >
                            </a-select>
                        </a-form-item>
                        <!-- 打印 -->
                        <a-form-item label="内容" v-if="toolName == 'echo'">
                            <a-textarea
                                v-decorator="['message', { rules: [{ required: true, message: '请输入内容' }] }]"
                                :rows="4"
                            />
                        </a-form-item>
                        <!-- 脚本 -->
                        <a-form-item label="内容" v-if="toolName == 'sh'">
                            <code-format style="margin-top:10px;" ref="codeFormat" v-model="content"></code-format>
                        </a-form-item>
                        <!-- git -->
                        <template v-else-if="toolName == 'git'">
                            <a-spin :spinning="spinning">
                            <a-form-item label="代码来源">
                                <a-radio-group v-model="gitFrom" @change="gitFromChange">
                                    <a-radio :value="1">外部Git地址</a-radio>
                                    <a-radio :value="2">OpsAny代码仓库</a-radio>
                                </a-radio-group>
                            </a-form-item>
                            <a-form-item label="代码仓库">
                                <a-input
                                    v-if="gitFrom==1"
                                    @change="gitUrlChange"
                                    placeholder="请输入外部Git地址"
                                    v-decorator="['url', { rules: [{ required: true, message: '请输入外部Git地址', },{pattern:/^(http:\/\/)|(https:\/\/)|(git@)/,message:'请输入正确的Git地址'}] },]"
                                ></a-input>
                                <template v-else>
                                    <a-tooltip v-if="codeBaseError" placement="topLeft" :title="codeBaseErrorMessage">
                                        <a-select disabled placeholder="请选择代码仓库">
                                        </a-select>
                                    </a-tooltip>
                                    <a-select v-else placeholder="请选择代码仓库"
                                        v-decorator="[
                                            'url',
                                            { rules: [{ required: true, message: '请选择代码仓库' }] },
                                        ]"
                                    >
                                        <!-- <a-select-option v-for="item in repositoryList" :value="item.ssh_clone" :key="item.ssh_clone">{{item.ssh_clone}}</a-select-option> -->
                                        <a-select-option v-for="item in repositoryList" :value="item.http_clone" :key="item.http_clone">{{item.http_clone}}</a-select-option>
                                    </a-select>
                                </template>
                            </a-form-item>
                            <a-form-item label="凭据">
                                <a-tree-select style="width:450px;" dropdownClassName="resource-tree-select-stepModal2" @select="credentialChange" allowClear tree-default-expand-all showSearch 
                                    treeNodeFilterProp="title" :tree-data="credentialsList" placeholder="请选择凭据，请先填写代码仓库地址。"
                                    dropdownMatchSelectWidth v-decorator="['credentialsId', { rules: [{ required: gitFrom == 2?true:false, message: '请选择凭据' }] }]">
                                </a-tree-select>
                                <a-button @click="reload" :loading="btnLoading" type="link" icon="reload"></a-button>
                                <a @click="gotoCredentialManagement">去创建</a>
                            </a-form-item>
                            <a-form-item label="分支">
                                <a-input
                                    placeholder="请输入分支"
                                    v-decorator="[
                                        'branch',
                                        {
                                            rules: [{ required: true, message: '请输入分支', whitespace: true }],
                                            initialValue: 'master',
                                        },
                                    ]"
                                ></a-input>
                            </a-form-item>
                            </a-spin>
                        </template>
                        <!-- 睡眠 -->
                        <template v-else-if="toolName == 'sleep'">
                            <a-form-item label="时间">
                                <a-input-number
                                    style="width: 100%"
                                    v-decorator="['time', { rules: [{ required: true, message: '请输入凭据' }] }]"
                                    :min="1"
                                ></a-input-number>
                            </a-form-item>
                            <a-form-item label="单位">
                                <a-select
                                    v-decorator="['unit', { rules: [{ required: true, message: '请输入凭据' }] }]"
                                >
                                    <a-select-option value="SECONDS">秒</a-select-option>
                                    <a-select-option value="MINUTES">分</a-select-option>
                                    <a-select-option value="HOURS">时</a-select-option>
                                    <a-select-option value="DAYS">天</a-select-option>
                                </a-select>
                            </a-form-item>
                        </template>
                        <!-- 写文件 -->
                        <template v-else-if="toolName == 'writeFile'">
                            <a-form-item label="文件名">
                                <a-input
                                    v-decorator="['file', { rules: [{ required: true, message: '请输入代码仓库' }] }]"
                                ></a-input>
                            </a-form-item>
                            <a-form-item label="内容">
                                <a-textarea
                                    v-decorator="['text', { rules: [{ required: true, message: '请输入内容' }] }]"
                                    :rows="4"
                                />
                            </a-form-item>
                        </template>
                        <!-- 读文件 -->
                        <template v-else-if="toolName == 'readFile'">
                            <a-form-item label="文件名">
                                <a-input
                                    v-decorator="['file', { rules: [{ required: true, message: '请输入代码仓库' }] }]"
                                ></a-input>
                            </a-form-item>
                            <a-form-item label="编码">
                                <a-input
                                    v-decorator="[
                                        'encoding',
                                        { rules: [{ required: false, message: '请输入代码仓库' }] },
                                    ]"
                                ></a-input>
                            </a-form-item>
                        </template>
                        <!-- 人工确认 -->
                        <template v-else-if="toolName == 'input'">
                            <a-form-item label="描述信息">
                                <a-input
                                    placeholder="请输入描述信息"
                                    v-decorator="[
                                        'message',
                                        { rules: [{ required: true, message: '请输入描述信息' }] },
                                    ]"
                                ></a-input>
                            </a-form-item>
                            <a-form-item label="确认者">
                                <a-select mode="multiple" optionFilterProp="searchData" show-search placeholder="请选择确认者" v-decorator="[
                                    'submitter',{ rules: [{ required: true, message: '请选择确认者' }] },]">
                                    <a-select-option v-for="item in userList" :value="item.username" :searchData="item.searchData" :key="item.username">{{item.ch_name || item.username}}({{item.username}})</a-select-option>
                                </a-select>
                            </a-form-item>
                            <a-form-item label="唯一标识">
                                <a-input disabled v-decorator="['id',{ rules: [{ required: true, message: '请输入唯一标识' }] },]">
                                </a-input>
                            </a-form-item>
                        </template>
                        <!-- 上传制品 -->
                        <template v-else-if="toolName == 'nexusArtifactUploader'">
                            <a-form-item label="选择制品库类型">
                                <a-radio-group v-model="nexusFrom">
                                    <a-radio :value="1">OpsAny制品仓库</a-radio>
                                    <a-radio :value="2">Nexus仓库</a-radio>
                                </a-radio-group>
                            </a-form-item>
                            <a-row v-if="nexusFrom == 2" :gutter="[16,16]">
                                <a-col :span="12">
                                    <a-form-item label="Nexus版本">
                                        <a-select placeholder="请选择Nexus版本" v-decorator="[
                                        'nexusVersion',{ rules: [{ required: true, message: '请选择Nexus版本' }] },]">
                                            <a-select-option value="NEXUS2">NEXUS2</a-select-option>
                                            <a-select-option value="NEXUS3">NEXUS3</a-select-option>
                                        </a-select>
                                    </a-form-item>
                                </a-col>
                                <a-col :span="12">
                                    <a-form-item label="协议类型">
                                        <a-select placeholder="请选择协议类型" v-decorator="[
                                        'protocol',{ rules: [{ required: true, message: '请选择协议类型' }] },]">
                                            <a-select-option value="HTTP">HTTP</a-select-option>
                                            <a-select-option value="HTTPS">HTTPS</a-select-option>
                                        </a-select>
                                    </a-form-item>
                                </a-col>
                            </a-row>
                            <a-form-item v-if="nexusFrom == 2" label="Nexus地址">
                                <a-input
                                    placeholder="请输入Nexus地址"
                                    v-decorator="['nexusUrl',{ rules: [{ required: true, message: '请输入Nexus地址' }] },]"
                                ></a-input>
                            </a-form-item>
                            <a-form-item label="凭证">
                                <a-select placeholder="请选择凭证" 
                                    v-decorator="['credentialsId',{ rules: [{ required: true, message: '请选择凭证' }] },]">
                                </a-select>
                            </a-form-item>
                            <a-form-item label="制品仓库">
                                <a-input
                                    placeholder="请选择制品仓库"
                                    v-decorator="['repository',{ rules: [{ required: true, message: '请选择制品仓库' }] },]"
                                ></a-input>
                            </a-form-item>
                            <label class="ant-form-item-required ant-form-item-label">上传文件</label>
                            <div class="file_box" v-for="(item,index) in fileList" :key="index">
                                <a-form-item label="文件目录">
                                    <a-input placeholder="请输入文件目录" v-decorator="['item.artifactId',{ rules: [{ required: true, message: '请输入文件目录' }] },]"></a-input>
                                </a-form-item>
                                <a-form-item label="文件类型">
                                    <a-input placeholder="请输入文件类型" v-decorator="['item.type',{ rules: [{ required: true, message: '请输入文件类型' }] },]"></a-input>
                                </a-form-item>
                                <a-form-item label="文件">
                                    <a-input placeholder="请输入文件" v-decorator="['item.file',{ rules: [{ required: true, message: '请输入文件' }] },]"></a-input>
                                </a-form-item>
                            </div>
                            <a-button @click="addFile" icon="plus">添加</a-button>
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

// import { getProjects, getBranch } from '@/api/gitlab.js'
import { getRepository } from "@/api/gitlab-repository-url.js"
import { getUserList } from '@/api/assemblyLine'
import { v4 as createUid } from "uuid";
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
            // 凭据选选项
            allCredentialsList: [
                { value:"Username with password", title:"密码验证", children:[], selectable:false,},
                { value:"GitLab API token", title:"GitLab令牌", children:[], selectable:false,},
                { value:"SSH Username with private key", title:"SSH密钥验证", children:[], selectable:false,},
                { value:"Secret text", title:"密钥文本", children:[], selectable:false,},
            ],
            credentialsList:[],

            // gitlab选项
            projectsList: [],
            // 分支选项
            branchList: [],
            // 标题
            modalTitle: '新增步骤',

            gitFrom: 1, //git代码来源  1为外部   2为opsany代码仓库
            repositoryList: [], //代码仓库数据
            btnLoading: false,
            spinning: false,
            nexusFrom: 1,
            
            fileList:[{ artifactId:"", type:"", file:"" }],
            codeBaseError: false,
            codeBaseErrorMessage: "",
            isPrivate: false, //私人凭证
            content: "", //执行脚本的内容
            url1: "",
            url2: "",
            credentials1:"",
            credentials2:"",
            urlType: "",
            userList: [],
        }
    },
    props: ['treeData', 'pipelineData', 'environmentList'],
    mounted() {
        this.getPostData()
    },
    methods: {
        uuid() {
            const uuid = createUid()
            this.$nextTick(()=>{
                this.form1.setFieldsValue({
                    id: uuid,
                })
            })
        },
        getUserListData() {
            getUserList().then(res =>{
                res.data.map(item =>{
                    item.searchData = (item.ch_name || "" )+ item.username
                })
                this.userList = res.data
            })
        },
        // 跳转到凭证管理
        gotoCredentialManagement() {
            let routeUrl = this.$router.resolve({
                path: "/setting/credentialManagement",
            })
            window.open(routeUrl.href, '_blank');
        },
        // 修改仓库地址
        gitUrlChange(event) {
            let url = event?.target?.value || event
            let reg_http = /^http/
            let reg_git = /^git@/
            // 判断之前的urlType类型如果相同credentialsId不变，如果不通则清空
            if(reg_http.test(url)) {
                if(this.urlType !="http") {
                    this.form1.setFieldsValue({
                        credentialsId: undefined,
                    })
                }
                this.credentialsList = [this.allCredentialsList[0]]
                this.urlType = "http"
            } else if(reg_git.test(url)) {
                if(this.urlType !="git") {
                    this.form1.setFieldsValue({
                        credentialsId: undefined,
                    })
                }
                this.credentialsList = [this.allCredentialsList[2]]
                this.urlType = "git"
            } else {
                this.credentialsList = []
                this.form1.setFieldsValue({
                    credentialsId: undefined,
                })
            }         
        },
        // 获取代码仓库数据
        getRepositoryData() {
            return getRepository().then(res => {
                this.repositoryList = res.data
            }).catch(res=>{
                this.codeBaseError = true
                this.codeBaseErrorMessage = res.message
            })
        },
        reload() {
            this.btnLoading = true
            this.getCredentialsData(true)
        },
        // 获取凭据数据
        getCredentialsData(showMessage) {
            return getCredentials({
                all_data: 'true',
            }).then((res) => {
                if (res.code == 200 && res.data) {
                    this.allCredentialsList = this.$options.data.call(this).allCredentialsList
                    res.data.forEach(item => {
                        item.value = item.credentials_id
                        item.key = item.credentials_id
                        item.title = `${item.name}(${item.credentials_id})`
                        let obj = this.allCredentialsList.find(ele => {
                            return ele.value == item.typeName
                        })
                        if(obj) {
                            obj.children.push(item)
                        }
                    })
                    if(showMessage) {
                        this.$message.success(res.message)
                    }
                }
            }).finally(()=>{
                this.btnLoading = false
                this.allCredentialsList.map(item =>{
                    item.number = item.children.length
                    item.title = item.title + "("+ item.number +")"
                })
                let url = this.form1.getFieldValue("url")
                let reg_http = /^http/
                let reg_git = /^git@/
                this.$nextTick(()=>{
                    if(reg_http.test(url)) {
                        this.credentialsList = [this.allCredentialsList[0]]
                    } else if(reg_git.test(url)) {
                        this.credentialsList = [this.allCredentialsList[2]]
                    } else {
                        this.credentialsList = []
                    }
                })  
            })
        },
        // 获取gitlab项目
        getProjectsData() {
            getProjects().then((res) => {
                if (res.code == 200 && res.data) {
                    this.projectsList = res.data
                }
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
            // 如果是git步骤，获取相关接口
            if (step.name == 'git') {
                this.spinning = true
                // 获取代码仓库平台的代码仓库数据
                this.getRepositoryData().finally(res => {
                    // 获取凭据
                    this.getCredentialsData().finally(() => {
                        this.spinning = false
                        if (step.isEdit) {
                            if(this.activeStep.arguments[0]?.value?.value.indexOf("http://oauth2:$GITLAB_ACCESS_KEY@")>-1){
                                this.isPrivate = true
                                this.gitFrom = 2
                                let url = this.activeStep.arguments[0].value.value.replace("http://oauth2:$GITLAB_ACCESS_KEY@","http://")
                                this.form1.setFieldsValue({url:url})
                                let credential = this.environmentList.find(item=>{
                                    return item.key == "GITLAB_ACCESS_KEY"
                                })
                                console.log(credential)
                                if(credential) {
                                    this.form1.setFieldsValue({credentialsId:credential.value.arguments[0].value})
                                }
                            } else {
                                let url = this.repositoryList.find(item => {
                                    return item.http_clone == this.activeStep.arguments[2]?.value?.value || item.ssh_clone == this.activeStep.arguments[2]?.value?.value
                                })
                                if (url) {
                                    this.gitFrom = 2
                                    this.urlType = "http"
                                } else {
                                    this.gitFrom = 1
                                }
                            }
                        }
                    })
                })
            } else if(step.name == 'sh') {
                this.$nextTick(function () {
                    step.arguments.map((item) => {
                        if(item.key == 'script') {
                            this.content = item.value.value
                        }
                    })
                })
            } else if(step.name == 'input') {
                this.getUserListData()
            }
            if (step.isEdit) {
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
                this.modalTitle = this.tool.title
                if (step.name == 'git') {

                } else if(step.name == 'input') {
                    let flag = step.arguments.find(item =>{
                        return item.key == "id"
                    })
                    if(!flag) {
                        this.uuid()
                    }
                }
                this.$nextTick(function () {
                    step.arguments.map((item) => {
                        this.form1.setFieldsValue({ [item.key]: item.value.value })
                        if(item.key == "credentialsId") {
                            this.form1.setFieldsValue({ [item.key]: item.value.value || undefined })
                        } else if(item.key == 'script') {
                            this.content = item.value.value
                        } else if(item.key == "submitter" && step.name == "input") {
                            if(item.value?.value) {
                                this.form1.setFieldsValue({ submitter:item.value?.value.split(",") })
                            } else {
                                this.form1.setFieldsValue({ submitter: []})
                            }
                        }
                    })
                })
            } else {
                let option = step
                this.modalTitle = option.title
                this.isAdd = true
                this.selectedKey = [option.name]
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
                // 添加人工确认步骤生成uuid
                if(step.name == 'input') {
                    this.uuid()
                }
                this.stepmodel = true
                // 打开弹框默认选echo并在右侧文本框填入信息
                this.toolName = option.name
                this.treeData.map((item) => {
                    item.children.map((ele) => {
                        if (ele.name == option.name) {
                            this.tool = ele
                        }
                    })
                })
                this.treeSelect([option.name],{node:{dataRef:option}})
            }
        },
        // 步骤提交
        stepHandleOk() {
            this.form1.validateFields((err) => {
                if(err) {
                    return false
                }
                let obj = JSON.parse(JSON.stringify({ name: this.tool.name, arguments: this.tool.arguments }))
                let name = this.tool.name
                if (name == 'echo' || name == 'sh') {
                    obj.arguments.map((item) => {
                        item.value.value = this.form1.getFieldValue(item.key)
                        if(item.key == 'script') {
                            item.value.value = this.content
                        }
                    })
                } else if (name == 'git') {
                    if(this.isPrivate) {
                        let value = this.form1.getFieldValue("credentialsId")
                        let environment = {
                            key:"GITLAB_ACCESS_KEY",
                            value:{
                                name: "credentials",
                                arguments:[{ isLiteral: true, value: value }],
                            }
                        }
                        this.$emit("updateEnvironment",environment)
                        let url = this.form1.getFieldValue("url")
                        let str = url.replace("http://","http://oauth2:$GITLAB_ACCESS_KEY@")
                        obj.arguments = [
                            {
                                key: "url",
						        value: {
						        	value: str,
						        	isLiteral: true
						        }
                            },
                        ]
                        if(this.form1.getFieldValue("branch")) {
                            obj.arguments.push(
                                {
                                    key: "branch",
						            value: {
						            	value: this.form1.getFieldValue("branch"),
						            	isLiteral: true,
						            }
                                }
                            )
                        }
                    } else {
                        obj.arguments.map((item) => {
                            item.value.value = this.form1.getFieldValue(item.key)
                            if(item.key == "credentialsId") {
                                item.value.value = this.form1.getFieldValue(item.key) || ""
                            }
                        })
                    }

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
                    // 多选转换
                    let arr = this.form1.getFieldValue('submitter')
                    obj.arguments = [
                        {
                            key: 'message',
                            value: {
                                isLiteral: true,
                                value: this.form1.getFieldValue('message'),
                            },
                        },
                        {
                            key: 'submitter',
                            value: {
                                isLiteral: true,
                                value: arr.join(","),
                            },
                        },
                        {
                            key: 'id',
                            value: {
                                isLiteral: true,
                                value: this.form1.getFieldValue('id'),
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
                        steps = parallel.branches[0].steps
                    }

                    steps.push(obj)
                    this.stepmodel = false
                } else {
                    // console.log(obj)
                    delete this.activeStep.isEdit
                    this.activeStep.name = obj.name
                    this.activeStep.arguments = obj.arguments
                    // this.activeStep.arguments.map((item) => {
                    //     item.value.value = this.form1.getFieldValue(item.key) || ''
                    // })
                    this.stepmodel = false
                    if (this.islast) {
                        if (this.form1.getFieldValue('posttype') != this.activeCondition.condition) {
                            let condition = this.pipelineData.pipeline.post.conditions.find((item) => {
                                return item.condition == this.activeCondition.condition
                            })
                            let steps = condition.branch.steps
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
            this.gitFrom = 1
            this.nexusFrom = 1
            this.codeBaseError = this.$options.data.call(this).codeBaseError
            this.credentialsList = this.$options.data.call(this).credentialsList
            this.allCredentialsList = this.$options.data.call(this).allCredentialsList
            this.isPrivate = this.$options.data.call(this).isPrivate
            this.fileList = this.$options.data.call(this).fileList
            this.url1 = ""
            this.url2 = ""
            this.credentials1 = ""
            this.credentials2 = ""
            this.urlType = ""
            this.content = ""

            delete this.activeStep.isEdit
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
        gitFromChange(event) {
            let val = event.target.value
            if(val == 2) {
                // this.urlType = "http"
                this.url1 = this.form1.getFieldValue("url")
                this.credentials1 = this.form1.getFieldValue("credentialsId")
                this.form1.setFieldsValue({ url: this.url2 || undefined })
                this.form1.setFieldsValue({ credentialsId: this.credentials2 || undefined })
                // this.gitUrlChange(this.url2)
                this.credentialsList = [this.allCredentialsList[0]]
            } else if(val == 1) {
                this.url2 = this.form1.getFieldValue("url")
                this.credentials2 = this.form1.getFieldValue("credentialsId")
                this.form1.setFieldsValue({ url: this.url1 || undefined })
                this.form1.setFieldsValue({ credentialsId: this.credentials1 || undefined })
                this.gitUrlChange(this.url1)
            }
            // 切换到内部代码仓库自动选择私钥
            // this.$nextTick(() => {
            //     if (val == 2) {
            //         let credential = this.credentialsList[3].children.find(item => {
            //             return item.is_private == 1
            //         })
            //         if (credential) {
            //             this.form1.setFieldsValue({ credentialsId: credential.credentials_id })
            //             this.isPrivate = true
            //         }
            //     }
            // })  
        },
        credentialChange(val,option) {
            if(option?.dataRef.is_private == 1 && this.gitFrom == 2) {
                this.isPrivate = true
            } else {
                this.isPrivate = false
            }
        },
        addFile() {
            this.fileList.push({ artifactId:"", type:"", file:"" })
        }
    },
    components: {
    }
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
        width: 180px;
    }
    .right {
        width: 500px;
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
        padding: 20px 30px;
        width: 620px;
        max-height: 600px;
        overflow-y: auto;
        .ant-form-item-label {
            text-align: left;
        }
    }
}
.file_box{
    border:1px solid #e8e8e8;
    border-radius: 5px;
    padding: 10px;
    background: #F6F8FA;
    margin:0 0 20px 0;
}
</style>
<style lang="less">
.resource-tree-select-stepModal2 {
    max-height: 400px !important;
}
</style>
<style>
.resource-tree-select-stepModal2 .ant-select-tree-switcher {
	position: relative;
}
.resource-tree-select-stepModal2 .ant-select-tree-switcher_open::before,
.resource-tree-select-stepModal2 .ant-select-tree-switcher_close::before {
	content: "";
	position: absolute;
	right: -490px;
	top: 0;
	left: 0;
	bottom: 0;
}
</style>
