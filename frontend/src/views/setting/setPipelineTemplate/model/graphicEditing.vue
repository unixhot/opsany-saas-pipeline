<template>
    <!-- 图形编辑 graphicEditing -->
    <div>
        <a-button @click="$refs.EnvironmentVariable.onShow(pipelineData.pipeline.environment)" style="position:absolute;right:0px;top:10px;">设置环境变量</a-button>
        <!-- 一二三级步骤分别为stage(阶段)、parallelstage(平行阶段)、step(步骤)
            一级步骤之间的连线由.stage:after生成
            竖线由.stage:before生成
            二级步骤和竖线之间的虚线由.parallelstage:before生成
            三级步骤和竖线之间的虚线由.step:before生成
         -->
        <div class="pipeline" v-if="pipelineData.pipeline&&pipelineData.pipeline.stages">
            <div class="stage firststage">
                <div class="parallelstage">
                    <h4 class="title">
                        <span class="serial">
                            <a-icon style="font-size:16px;" type="caret-right" />
                        </span>
                        <span class="name">开始</span>
                    </h4>
                </div>
                <a-icon @click="addstage(-1)" class="addstage" type="plus" />
            </div>

            <div class="stage" v-for="(stage,stageindex) in pipelineData.pipeline.stages" :key="stageindex">
                <template v-if="stage.parallel">
                    <div class="parallelstage" v-for="(parallelstage,parallelindex) in stage.parallel" :key="parallelindex">
                        <h4 class="title" @click="editParallel(stageindex,parallelindex,parallelstage)">
                            <span class="serial">{{stageindex+1}}-{{parallelindex+1}}</span>
                            <span :title="parallelstage.name" class="name">{{parallelstage.name}}</span>
                            <a-icon v-if="parallelstage.branches&&parallelstage.branches[0].steps&&parallelstage.branches[0].steps.length<1" style="color:red;margin:0 0 0 5px;" type="exclamation-circle" />
                            <a-icon class="deleteparallel" @click.stop="delectParallelstage(stageindex,parallelindex)" type="close-circle" />
                            <a-icon class="caret" type="caret-right" />
                        </h4>
                        <template v-if="parallelstage.branches">
                            <p @click="editstep(stageindex,parallelindex,step)" v-for="(step,stepindex) in parallelstage.branches[0].steps" :key="stepindex" :class="{step:true,step1:isShow(step)}">
                                <a-tooltip :title="!isShow(step)?'当前版本暂不支持修改！':''">
                                    <span class="span1">
                                        <a-icon type="file" />
                                    </span>
                                    <span class="span2">{{chName(step)}}</span>
                                    <a-icon class="deletestep" @click.stop="delectStep(stageindex,parallelindex,stepindex)" type="close-circle" />
                                    <span class="round"></span>
                                </a-tooltip>
                            </p>
                        </template>
                        <!-- <a-icon @click="addstep(stageindex,parallelindex)" class="addstep" type="plus" /> -->
                        <span>
                            <a-cascader :options="options" @change="(val,option) => onCascaderChange(val,option,stageindex,parallelindex)">
                                <a-icon class="addstep" type="plus" />
                            </a-cascader>
                        </span>
                    </div>
                    <p @click="addParallelstage(stageindex,stage)" class="addParallelstage">
                        <a-icon type="plus" />增加并行阶段
                        <a-icon class="caret" type="caret-right" />
                    </p>
                </template>
                <a-icon @click="addstage(stageindex)" class="addstage" type="plus" />
            </div>

            <div class="stage laststage">
                <div class="parallelstage">
                    <h4 class="title">
                        <span class="serial ">
                            <span style="width:15px;height:15px;border:2px solid #fff;display:inline-block;border-radius:50%;margin-top:12px;"></span>
                        </span>
                        <span class="name">结束</span>
                        <a-icon class="caret" type="caret-right" />
                    </h4>
                    <template v-if="pipelineData.pipeline.post&&pipelineData.pipeline.post.conditions">
                        <div v-for="(condition,conditionindex ) in pipelineData.pipeline.post.conditions" :key="conditionindex" class="condition">
                            <p @click="editstep(-1,conditionindex,step,stepindex)" v-for="(step,stepindex) in condition.branch.steps" :key="stepindex" :class="{step:true,step1:isShow(step)}">
                                <a-tooltip :title="!isShow(step)?'当前版本暂不支持修改！':''">
                                    <span class="span1">
                                        <a-icon type="file" />
                                    </span>
                                    <span class="span2">{{chName(step)}}</span>
                                    <a-icon class="deletestep" @click.stop="delectStep(stageindex,parallelindex,stepindex)" type="close-circle" />
                                    <span class="round"></span>
                                </a-tooltip>
                            </p>
                        </div>
                    </template>
                    <!-- <a-icon @click="addstep(-1,-1)" class="addstep" type="plus" /> -->
                    <span>
                        <a-cascader :options="options" @change="(val,option) => onCascaderChange(val,option,-1,-1)">
                            <a-icon class="addstep" type="plus" />
                        </a-cascader>
                    </span>
                </div>
            </div>
        </div>

        <!-- 新增or修改阶段 -->
        <a-modal :title="add_or_edit_stage=='add'?'新增阶段':(add_or_edit_stage=='edit'?'修改阶段':'新增平行阶段')" v-model="stagemodel" @ok="stageHandleOk" @cancel="stageCancel">
            <a-form :form="stageform" :label-col="{ span: 5 }" :wrapper-col="{ span: 15 }">
                <a-form-item label="阶段名称">
                    <a-input v-decorator="[
                    'name',
                    { rules: [{ required: true, message: '请输入名称' }] },]">
                    </a-input>
                </a-form-item>
                <a-form-item label="超时时间">
                    <a-input-group compact>
                        <a-input-number style="width: 175px" placeholder="请输入超时时间" :formatter="value => `${value}`.replace(/\D/g,'')"
                        :parser="value => value.replace(/\D/g,'')" v-decorator="['timeout_number', { rules: [{ required: false, }] },]">
                        </a-input-number>
                        <a-select style="width: 120px" placeholder="单位" v-decorator="['timeout_unit', { rules: [{ required: false, }] },]">
                            <a-select-option value="SECONDS">秒</a-select-option>
                            <a-select-option value="MINUTES">分</a-select-option>
                            <a-select-option value="HOURS">时</a-select-option>
                            <a-select-option value="DAYS">天</a-select-option>
                        </a-select>
                    </a-input-group>
                </a-form-item>
            </a-form>
        </a-modal>
        <StepModel :environmentList.sync="environmentList" :pipelineData.sync="pipelineData" @updateEnvironment="(environment)=>{pipelineData.pipeline.environment.push(environment)}" :treeData.sync="treeData" ref="StepModel"></StepModel>
        <EnvironmentVariable @update="update" ref="EnvironmentVariable"></EnvironmentVariable>
    </div>
</template>

<script>
import { toPepiline } from "@/api/jenkinsTransform.js"
import { getPipelineTool } from "@/api/pipeline-tool.js"
import StepModel from "./stepModal2.vue"
import { getReconfig, editReconfig } from "@/api/reconfig"
import EnvironmentVariable from "./environmentVariable.vue"
import storage from 'store'
export default {
    data() {
        return {
            // 由pipeline代码转换的json(不能直接使用)
            pipelineJson: {
                "pipeline": {
                    "stages": [{
                        "name": "执行拉取代码脚本",
                        "branches": [{
                            "name": "default",
                            "steps": [{
                                "name": "echo",
                                "arguments": [{
                                    "key": "message",
                                    "value": {
                                        "isLiteral": true,
                                        "value": "执行拉取代码脚本..."
                                    }
                                }]
                            },
                            {
                                "name": "sh",
                                "arguments": [{
                                    "key": "script",
                                    "value": {
                                        "isLiteral": true,
                                        "value": "/bin/bash /web_project/agile/agile-project/jenkins-deploy-agile.sh"
                                    }
                                }]
                            }
                            ]
                        }]
                    },
                    {
                        "name": "重启项目",
                        "branches": [{
                            "name": "default",
                            "steps": [{
                                "name": "echo",
                                "arguments": [{
                                    "key": "message",
                                    "value": {
                                        "isLiteral": true,
                                        "value": "重启项目..."
                                    }
                                }]
                            },
                            {
                                "name": "sh",
                                "arguments": [{
                                    "key": "script",
                                    "value": {
                                        "isLiteral": true,
                                        "value": "supervisorctl restart agile"
                                    }
                                }]
                            },
                            {
                                "name": "sh",
                                "arguments": [{
                                    "key": "script",
                                    "value": {
                                        "isLiteral": true,
                                        "value": "ps aux | grep agile-backend"
                                    }
                                }]
                            }
                            ]
                        }]
                    }
                    ],
                    "agent": {
                        "type": "any"
                    }
                }
            },
            // 由pipelineJson转换而来，用于生成和操作图形
            pipelineData: {},
            // 新增or修改阶段(一级步骤)的弹框显示
            stagemodel: false,
            stageform: this.$form.createForm(this, { name: 'stageform' }),
            // 选中的阶段的index
            operationStageIndex: -3,
            treeData: [],
            // add代表新增阶段，edit代表编辑阶段，addParallel代表新增平行阶段
            add_or_edit_stage: "",
            options: [],
            environmentList: [], // 环境变量参数(git步骤回填时寻找凭证时使用)
        }
    },
    mounted() {
        this.getPipelineTool()
        this.pipelineJson = this.fathertosubpipelineJson
        this.pipelineData = {
            pipeline: {
                stages: [],
                environment: [],
                post: {
                    conditions: [{
                        condition: "always",
                        branch: {
                            name: "default",
                            steps: [],
                        },
                    }, {
                        condition: "aborted",
                        branch: {
                            name: "default",
                            steps: [],
                        },
                    }, {
                        condition: "failure",
                        branch: {
                            name: "default",
                            steps: [],
                        },
                    }, {
                        condition: "success",
                        branch: {
                            name: "default",
                            steps: [],
                        },
                    }, {
                        condition: "unsuccessful",
                        branch: {
                            name: "default",
                            steps: [],
                        },
                    }, {
                        condition: "cleanup",
                        branch: {
                            name: "default",
                            steps: [],
                        },
                    }]
                }
            }
        }
        // console.log(this.pipelineJson)
        // 由pipeline转成的json中，当stage里有两个二级阶段和只有一个二级阶段结构不同，操作不便，进行处理使结构相同便于操作
        if (this.pipelineJson.pipeline && this.pipelineJson.pipeline.stages) {
            this.pipelineJson.pipeline.stages.map(stage => {
                if (stage.parallel) {
                    // let stageobj = {
                    //     name: stage.name,
                    //     options: stage.options,
                    // }
                    // stageobj.parallel = stage.parallel
                    let stageobj = {...stage}
                    this.pipelineData.pipeline.stages.push(stageobj)
                } else {
                    let stageobj = {
                        name: stage.name,
                        parallel: []
                    }
                    stageobj.parallel.push(stage);
                    this.pipelineData.pipeline.stages.push(stageobj)
                }
            })
        }
        if (this.pipelineJson.pipeline && this.pipelineJson.pipeline.post) {
            this.pipelineJson.pipeline.post.conditions.map(item => {
                this.pipelineData.pipeline.post.conditions.map(ele => {
                    if (item.condition == ele.condition) {
                        ele.branch = item.branch
                    }
                })
            })
        }
        if (this.pipelineJson.pipeline && this.pipelineJson.pipeline.environment) {
            this.pipelineJson.pipeline.environment.map(item => {
                this.pipelineData.pipeline.environment.push(item)
            })
            this.environmentList = this.pipelineData.pipeline.environment
        }


        console.log(this.pipelineData.pipeline, this.fathertosubpipelineJson)
    },
    computed: {

    },
    props: ["fathertosubpipelineJson"],
    methods: {
        update(environmentData) {
            this.pipelineData.pipeline.environment = environmentData
        },
        // 将名称转换为中文
        chName(step) {
            if (step.name == "git") {
                return "拉取代码"
            } else if (step.name == "echo") {
                return "打印消息"
            } else if (step.name == "sh") {
                return "执行Shell脚本"
            } else if (step.name == "sleep") {
                return "睡眠"
            } else if (step.name == "writeFile") {
                return "写文件"
            } else if (step.name == "readFile") {
                return "读文件"
            } else if (step.name == "codingArtifactsGeneric") {
                return "上传到制品库"
            } else if (step.name == "input") {
                return "人工确认"
            } else if (step.name == "nexusArtifactUploader") {
                return "上传制品"
            } else {
                return step.name
            }
        },
        isShow(step) {
            let arr = ["git","echo","sh","sleep","writeFile","readFile","codingArtifactsGeneric","input","nexusArtifactUploader"]
            let isShow = arr.find(item => item == step.name)
            if(isShow) {
                return true
            }
        },
        // 删除步骤(三级)
        delectStep(stageindex, parallelindex, stepindex) {
            let _this = this;
            this.$confirm({
                title: "确认删除该步骤吗?",
                okType: "danger",
                onOk() {
                    if (stageindex > -1) {
                        let state = _this.pipelineData.pipeline.stages[stageindex]
                        let parallel = state.parallel[parallelindex]
                        parallel.branches[0].steps.splice(stepindex, 1)
                    } else {
                        _this.pipelineData.pipeline.post.conditions[parallelindex].branch.steps.splice(stepindex, 1)
                    }
                }
            })
        },
        // 删除平行阶段(二级)
        delectParallelstage(stageindex, parallelindex) {
            let _this = this;
            this.$confirm({
                title: "确认删除该阶段吗?",
                okType: "danger",
                onOk() {
                    let state = _this.pipelineData.pipeline.stages[stageindex]
                    state.parallel.splice(parallelindex, 1)
                    // 如果某阶段下的平行阶段数为零，将该阶段删除
                    _this.pipelineData.pipeline.stages.map((stage, index) => {
                        if (stage.parallel.length == 0) {
                            _this.pipelineData.pipeline.stages.splice(index, 1)
                        }
                    })
                }
            })
        },
        // 修改平行阶段名称
        editParallel(stageindex, parallelindex, parallelstage) {
            this.stagemodel = true
            this.add_or_edit_stage = "edit"
            this.operationParallel = parallelstage
            this.$nextTick(function () {
                this.stageform.setFieldsValue({ name: parallelstage.name })
                // 超时时间回填
                if(parallelstage.options?.options?.length > 0) {
                    let timeout = parallelstage.options?.options.find(item => {
                        return item.name == "timeout"
                    })
                    if(timeout) {
                        this.stageform.setFieldsValue({ timeout_number: timeout.arguments[0].value.value })
                        this.stageform.setFieldsValue({ timeout_unit: timeout.arguments[1].value.value })
                    } else {
                        this.stageform.setFieldsValue({ timeout_unit: "SECONDS" })
                    }
                } else {
                    this.stageform.setFieldsValue({ timeout_unit: "SECONDS" })
                }
            })
        },
        // 新增平行阶段
        addParallelstage(stageindex, stage) {
            this.stagemodel = true
            this.add_or_edit_stage = "addParallel"
            this.operationStage = stage;
            this.$nextTick(function () {
                this.stageform.setFieldsValue({ timeout_unit: "SECONDS" })
            })
        },
        // 获取命令类型
        getPipelineTool() {
            getPipelineTool().then(res => {
                if (res.code == 200 && res.data) {
                    this.treeData = []
                    this.options = []
                    // 分类
                    res.data.map((item, index) => {
                        let parent = {
                            key: "n" + index,
                            title: item.tool_type,
                            disabled: true,
                            children: [],
                        }
                        // 命令
                        item.data.map(ele => {
                            let child = ele
                            child.key = ele.name
                            child.title = ele.tool_name
                            // 将arguments中的isLiteral转为Boolean型
                            child.arguments.map(argument => {
                                // console.log(argument.value)
                                argument.value.isLiteral = argument.value.isLiteral == "true" ? true : false
                            })
                            parent.children.push(child)
                        })
                        this.treeData.push(parent)
                    })
                    // console.log(this.treeData)
                    res.data.map((item, index) => {
                        let parent = {
                            value: "n" + index,
                            label: item.tool_type,
                            children: [],
                        }
                        // 命令
                        item.data.map(ele => {
                            let child = ele
                            child.value = ele.name
                            child.label = ele.tool_name
                            child.arguments.map(argument => {
                                argument.value.isLiteral = (argument.value.isLiteral == "true" || argument.value.isLiteral == true)? true : false
                            })
                            parent.children.push(child)
                        })
                        this.options.push(parent)
                    })
                }
            })
        },
        // json转pipeline
        toPepiline(preserve) {
            for (let key in this.pipelineJson.pipeline){
                if(key !="stages" && key !="environment"){
                    this.pipelineData.pipeline[key] =this.pipelineJson.pipeline[key]
                }
            }
            if (this.pipelineData.pipeline.post) {
                // steps为空转pipeline会报错，清空step为空的condition
                let p = this.pipelineData.pipeline.post.conditions.filter((item, index) => {
                    return item.branch.steps.length > 0
                })
                this.pipelineData.pipeline.post.conditions = p

                if (this.pipelineData.pipeline.post.conditions.length == 0) {
                    delete this.pipelineData.pipeline.post
                }
            }
            // 去除单独的并行阶段
            this.pipelineData1 = JSON.parse(JSON.stringify(this.pipelineData))
            if(this.pipelineData1.pipeline.environment.length == 0) {
                delete this.pipelineData1.pipeline.environment
            }
            this.pipelineData1.pipeline.stages.map(stage => {
                if (stage.parallel.length == 1) {
                    // stage.name = stage.parallel[0].name
                    // stage.options = stage.parallel[0].options
                    // stage.branches = stage.parallel[0].branches
                    // delete stage.parallel
                    for(let key in stage.parallel[0]) {
                        stage[key] = stage.parallel[0][key]
                    }
                    delete stage.parallel
                }
            })
            // 转换字符串格式的json
            let n = JSON.stringify(this.pipelineData1)
            let formdata = new FormData()
            formdata.append("json_file", n)
            return toPepiline(formdata).then(res => {
                if (res.code == 200 && res.data) {
                    if (preserve) {
                        this.$emit("subtofatherPepiline", res.data, true)
                    } else {
                        this.$emit("subtofatherPepiline", res.data, true)
                    }
                }
            }).catch(res => {
                this.$emit("subtofatherPepiline", res.data, false)
            })
        },
        // 新增or修改一个state
        addstage(index) {
            this.operationStageIndex = index;
            this.stagemodel = true;
            this.add_or_edit_stage = "add"
            this.$nextTick(function () {
                this.stageform.setFieldsValue({ timeout_unit: "SECONDS" })
            })
        },
        // 阶段提交提交
        stageHandleOk() {
            this.stageform.validateFields((err, value) => {
                if (!err) {
                    let timeoutJson = {
                        "name": "timeout",
                        "arguments": [
                            {
                                "key": "time",
                                "value": {
                                    "isLiteral": true,
                                    "value": value.timeout_number - 0
                                }
                            },
                            {
                                "key": "unit",
                                "value": {
                                    "isLiteral": true,
                                    "value": value.timeout_unit
                                }
                            }
                        ]
                    }
                    if (this.add_or_edit_stage == "add") {
                        let obj = {
                            name: value.name,
                            parallel: [{
                                name: value.name,
                                branches: [{
                                    name: "default",
                                    steps: []
                                }]
                            }]
                        }
                        if (value.timeout_number >= 0 && value.timeout_unit) {
                            obj.parallel[0].options = { options: [timeoutJson] }
                        }
                        this.pipelineData.pipeline.stages.splice(this.operationStageIndex + 1, 0, obj)
                    } else if (this.add_or_edit_stage == "edit") {
                        this.operationParallel.name = value.name
                        // 超时时间以及单位都有才生效
                        if (value.timeout_number >= 0 && value.timeout_unit) {
                            if (this.operationParallel.options) {
                                let timeout = this.operationParallel.options.options?.find(item =>{
                                    return item.name == "timeout"
                                })
                                if (timeout) {
                                    // 原本就有超时时间的情况,回填
                                    timeout.arguments[0].value.value = value.timeout_number - 0
                                    timeout.arguments[1].value.value = value.timeout_unit
                                } else {
                                    // 有options但没有超时时间的情况,添加timeout
                                    this.operationParallel.options.options?.push(timeoutJson)
                                }
                            } else {
                                // 没有options的情况，需要手动添加options
                                this.operationParallel.options = {
                                    "options": [timeoutJson]
                                }
                            }
                        }
                    } else if (this.add_or_edit_stage == "addParallel") {
                        let obj = {
                            name: value.name,
                            branches: [{
                                name: "default",
                                steps: []
                            }]
                        }
                        if (value.timeout_number >= 0 && value.timeout_unit) {
                            obj.options = { options: [timeoutJson] }
                        }
                        this.operationStage.parallel.push(obj)
                    }
                    this.stagemodel = false;
                    this.stageform.resetFields()
                    // console.log(this.pipelineData.pipeline)
                }
            })
        },
        // 阶段取消
        stageCancel() {
            this.stagemodel = false
            this.stageform.resetFields()
        },
        // 增加or修改
        addstep(stageindex, parallelindex, option) {
            // console.log(stageindex, parallelindex)
            this.$refs.StepModel.show(stageindex, parallelindex, option)
        },

        editstep(stageindex, parallelindex, step, stepindex) {
            if(this.isShow(step)) {
                step.isEdit = true
                this.$refs.StepModel.show(stageindex, parallelindex, step, stepindex)
            }
        },
        onCascaderChange(value,selectedOptions,stageindex, parallelindex) {
            this.addstep(stageindex, parallelindex,selectedOptions[1])
        },
    },
    components: {
        StepModel, EnvironmentVariable
    }
}
</script>

<style lang="less" scoped>
.pipeline {
    padding: 20px;
    margin: 10px 0 0 0;
    overflow-x: auto;
    width: 100%;
    white-space: nowrap;
    background: #f6f8fa;
    .stage {
        width: 200px;
        // border:1px dotted ;
        display: inline-block;
        position: relative;
        margin: 0 0 0 110px;
        vertical-align: top;
        &:after {
            width: 111px;
            height: 1px;
            content: '';
            background: #148aff;
            display: inline-block;
            position: absolute;
            top: 20px;
            left: 200px;
        }
        &:before {
            content: '';
            background: #ccc;
            border-left: 1px dashed #ccc;
            position: absolute;
            width: 1px;
            height: calc(100% - 40px);
            top: 20px;
            left: -25px;
        }
        .parallelstage:last-of-type {
            &:before {
                display: none;
            }
        }
        .parallelstage {
            padding: 0 0 30px 0;
            position: relative;
            &:before {
                content: '';
                width: 1px;
                height: 100%;
                background: #148aff;
                position: absolute;
                top: 20px;
                left: -25px;
            }
            .title {
                margin: 0;
                height: 40px;
                border: 1px solid #eee;
                border-radius: 5px;
                background: #fff;
                box-shadow: rgba(0, 0, 0, 0.098) 0px 1px 4px;
                .deleteparallel {
                    display: none;
                    color: #ccc;
                    margin: 0 0 0 3px;
                    position: absolute;
                    right: 10px;
                    top: 14px;
                }
                .caret {
                    position: absolute;
                    left: -9px;
                    top: 13.5px;
                    color: #148aff;
                }
                &:before {
                    content: '';
                    position: absolute;
                    display: inline-block;
                    width: 25px;
                    height: 1px;
                    background: #148aff;
                    left: -25px;
                    top: 20px;
                }

                &:hover {
                    cursor: pointer;
                    border: 1px solid #148aff;
                    .deleteparallel {
                        display: inline-block;
                        &:hover {
                            color: #333;
                        }
                    }
                }
                .serial {
                    background: #148aff;
                    color: #fff;
                    display: inline-block;
                    height: 38px;
                    width: 50px;
                    text-align: center;
                    line-height: 40px;
                    border-radius: 5px 0 0 5px;
                }
                .name {
                    padding: 0 0 0 10px;
                    display: inline-block;
                    width: 98px;
                    overflow: hidden;
                    white-space: nowrap;
                    text-overflow: ellipsis;
                    line-height: 38px;
                    height: 38px;
                    vertical-align: top;
                }
            }
            .step {
                border: 1px solid #e2e6ea;
                border-radius: 5px;
                height: 40px;
                line-height: 40px;
                margin: 20px 0 0 0px;
                background: #fff;
                position: relative;
                &:before {
                    position: absolute;
                    width: 1px;
                    content: '';
                    height: 20px;
                    top: -21px;
                    left: 20px;
                    background: #c2c6cb;
                }

                .span1 {
                    width: 36px;
                    height: 38px;
                    display: inline-block;
                    border-right: 1px solid #e2e6ea;
                    text-align: center;
                }

                .span2 {
                    width: 120px;
                    padding: 0 0 0 10px;
                    display: inline-block;
                }
                .deletestep {
                    display: none;
                    position: absolute;
                    right: 10px;
                    top: 14px;
                }
                .round {
                    position: absolute;
                    top: -4px;
                    left: 17px;
                    display: inline-block;
                    height: 7px;
                    width: 7px;
                    border: 1px solid #ccc;
                    border-radius: 50%;
                    background: #fff;
                }
                &:hover {
                    .deletestep {
                        display: inline-block;
                        color: #ccc;
                        &:hover {
                            color: #333;
                        }
                    }
                }
            }
            .step1 {
                cursor: pointer;
                &:hover {
                    border: 1px solid #09f;
                    .deletestep {
                        display: inline-block;
                        color: #ccc;
                        &:hover {
                            color: #333;
                        }
                    }
                }
            }
            .addstep {
                position: absolute;
                bottom: 20px;
                left: 100px;
                background: #fff;
                color: #09f;
                padding: 2px;
                font-size: 12px;
                border: 1px solid #09f;
                border-radius: 50%;
                &:hover {
                    background: #09f;
                    color: #fff;
                    border-radius: 50%;
                }
            }
        }
        .addParallelstage {
            border: 1px dashed #cbd1d9;
            height: 40px;
            line-height: 40px;
            margin: 0;
            text-align: center;
            cursor: pointer;
            position: relative;
            background: #fff;
            &:hover {
                border: 1px solid #09f;
            }
            &:before {
                content: '';
                position: absolute;
                display: inline-block;
                width: 25px;
                height: 1px;
                border-top: 1px dashed #cbd1d9;
                left: -25px;
                top: 20px;
            }
            .caret {
                position: absolute;
                left: -11px;
                top: 13.5px;
                color: #b3bbc6;
            }
        }
        .addstage {
            position: absolute;
            top: 11.5px;
            right: -64px;
            cursor: pointer;
            z-index: 8;
            background: #fff;
            border-radius: 50%;
            color: #09f;
            padding: 2px;
            border: 1px solid #09f;
            font-size: 12px;
            &:hover {
                background: #09f;
                color: #fff;
                border-radius: 50%;
            }
        }
    }
    .laststage {
        &:before {
            display: none;
        }
        &:after {
            width: 0;
        }
    }
    .firststage {
        margin: 0;
        .parallelstage::before {
            width: 0;
        }
        .parallelstage .title::before {
            display: none;
        }
    }
}
.pipeline {
    scrollbar-color: #e5e5e5 #f7f7f9; /* 滑块颜色  滚动条背景颜色 */
    scrollbar-width: thin; /* 滚动条宽度有三种：thin、auto、none */
}
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-button {
    display: none;
}

::-webkit-scrollbar-track-piece {
    background: #eee;
}
::-webkit-scrollbar-thumb {
    background: #aaa;
}
</style>>
