<template>
    <div>

        <content-header>
            <div slot="docs">将常用的流水线进行收藏，用于快速定位流水线。</div>
        </content-header>
        <a-card>
            <div class="content">
                <div class="content_left">
                    <a-spin v-if="showTree" :spinning="spinning">
                        <a-tree :show-line="true" :show-icon="false" :treeData="treeData" @select="onSelect" :selectedKeys="selectedKeys" :expandedKeys.sync="expandedKeys">
                            <template slot="title_name" slot-scope="row">
                                <div class="action_box">
                                    <a-tooltip placement="left">
                                        <template slot="title">{{ row.title }}</template>
                                        <span class="title">{{ row.title }}</span>
                                    </a-tooltip>
                                    <div class="action_box_right">
                                        <a-tag class="tree_tag">{{ row.tags_job_count }}</a-tag>
                                    </div>
                                </div>
                            </template>
                        </a-tree>
                        <a-empty v-if="treeData.length == 0"></a-empty>
                    </a-spin>
                    <a-skeleton style="padding: 10px" v-else />

                </div>
                <div class="content_right">
                    <div class="top_search">
                        <a-input-search v-model="tableQuery.search_data" @search="searchTable" :placeholder="language.search_placeholder" style="width: 300px;margin:0 10px 0 0" allowClear>
                            <a-select slot="addonBefore" style="width: 100px" v-model="tableQuery.search_type">
                                <a-select-option v-for="item in searchList" :value="item.key" :key="item.key">{{ item.name }}</a-select-option>
                            </a-select>
                        </a-input-search>
                        <a-button :loading="tableLoading" @click="reload" icon="reload" style="float: right">刷新</a-button>
                    </div>
                    <a-table :row-key="(record) => record.code" @change="tableChange" :loading="{spinning:tableLoading,tip:'正在加载中，请耐心等待...'}" :columns="columns" :dataSource="tableData" :pagination="{...tableQuery,showSizeChanger: true,showTotal: (total) => `共 ${total} 条数据`,showQuickJumper: true,
                        pageSizeOptions: ['10','20','40','50','100','150','200',],}" :scroll="{x:1000}">
                        <template slot="name" slot-scope="text, record">
                            <a v-if="record.can_log" :title="text" @click="$router.push({name:'executionLog',query:{appCode:record.application.code,job_name:record.name,...tableQuery,selectType:selectType,selectCode:selectCode,view_name:record.view_name,job_code:record.code,fromName:'myCollection'}})">{{text}}</a>
                            <span v-else>{{text}}</span>
                            <!-- <p class="ellipsis_dom" :title="record.description" style="margin:0;font-size:12px">{{record.description || '--'}}</p> -->
                        </template>
                        <template slot="status" slot-scope="text, record">
                            <span class="color_box">
                                <span v-if="text == 'SUCCESS'" style="color: #0ba360">
                                    <a-icon type="check-circle" theme="filled" />{{ language.succeeded }}
                                </span>
                                <span v-else-if="text == 'FAILURE'" style="color: red">
                                    <a-icon type="close-circle" theme="filled" />{{ language.failed }}
                                </span>
                                <span v-else-if="text == 'ABORTED'" style="color: #ffa800">
                                    <a-icon theme="filled" type="pause-circle" />{{ language.stop }}
                                </span>
                                <span v-else-if="text == 'WAITING'" style="color: #ffa800">
                                    <a-icon type="hourglass" />等待执行
                                </span>
                                <span v-else-if="text == 'UNSTABLE'" style="color: #ffa800">
                                    <a-icon theme="filled" type="exclamation-circle" />不稳定
                                </span>
                                <span v-else-if="text == 'PENDING'" style="">
                                    <a-icon type="clock-circle" />等待确认
                                </span>
                                <span v-else-if="record.build && record.build.building" style="color: #09f">
                                    <a-icon type="play-circle" theme="filled" />{{ language.executing }}
                                </span>
                                <span v-else-if="!(record.build && record.build.code)" style="color: #bbb">
                                    <a-icon type="minus-circle" theme="filled" />{{ language.no_execution }}
                                </span>
                                <span v-else>
                                    {{record.status}}
                                </span>
                            </span>
                        </template>
                        <template slot="last_run_number" slot-scope="text, record">
                            <span v-if="text">
                                <a v-if="record.can_log" @click="routerGoto(record)">#{{text}}</a>
                                <span v-else>#{{text}}</span>
                            </span>
                            <span v-else>--</span>
                        </template>
                        <template slot="last_run_username" slot-scope="text, record">
                            <span v-if="text">{{text}}</span>
                            <span v-else>--</span>
                        </template>
                        <template slot="action" slot-scope="text, record">
                            <a-spin :spinning="record.btnLoading">
                                <a-icon v-if="record.can_run" @click="immediatelyHandle(record)" title="执行" style="font-size:18px;" class="action_icon" theme="filled" type="play-circle" />
                                <span style="font-size:18px;margin:0 0 0 10px;">
                                    <a-icon v-if="record.tags" title="取消收藏" class="action_icon_hover" style="color: #ff9600" @click="collect(record)" type="star" theme="filled" />
                                    <a-icon v-else-if="!record.tags" title="收藏" class="action_icon_hover" type="star" @click="collect(record)" />
                                </span>
                                <a-dropdown v-if="record.can_update || record.can_log || record.can_delete">
                                    <a-icon class="action_icon_hover" style="font-size:18px;margin:0 0 0 10px;" type="more" />
                                    <a-menu slot="overlay">
                                        <a-menu-item v-if="record.can_update" @click="$router.push({path: '/applicationDelivery/assemblyLine/pipelineConfiguration',query: {name:record.name,appCode: record.application.code,...tableQuery,selectType:selectType,selectCode:selectCode,view_name:record.view_name,job_code:record.code,fromName:'myCollection'},})">
                                            {{language.edit}}
                                        </a-menu-item>
                                        <a-menu-item v-if="record.can_log" @click="$router.push({name:'executionLog',query:{appCode:record.application.code,job_name:record.name,...tableQuery,selectType:selectType,selectCode:selectCode,view_name:record.view_name,job_code:record.code,fromName:'myCollection'}})">
                                            历史记录
                                        </a-menu-item>
                                        <a-menu-item v-if="record.can_delete" @click="deleteAssemblyLine(record)">
                                            {{language.delete}}
                                        </a-menu-item>
                                    </a-menu>
                                </a-dropdown>
                            </a-spin>
                        </template>
                    </a-table>
                </div>
            </div>
            <!-- 新建流水线 -->
            <AddAssemblyLine @father="getTableData(true),getBusinessTreeData()" ref="AddAssemblyLine"></AddAssemblyLine>
            <!-- 立即执行弹框 -->
            <a-modal v-model="immediatelyModel" :title="language.execute" :okText="language.execute" @ok="immediatelyHandleOk" :confirmLoading="immediatelyConfirmLoading">
                <a-spin :spinning="modalLoading">
                    <a-form :form="immediateForm" :label-col="{ span: 0 }" :wrapper-col="{ span: 24 }">
                        <a-form-item v-for="(item, index) in string_parameter" :key="'s' + index" :label="language.label">
                            <a-input-group>
                                <a-input style="width: 130px" v-model="item.name" :disabled="true" />
                                <span style="
                                    width: 40px;
                                    float: left;
                                    text-align: center;
                                    line-height: 30px;
                                    border-bottom: 1px solid #ccc;
                                    border-top: 1px solid #ccc;
                                ">=</span>
                                <a-input v-decorator="[
                                    item.name,
                                    {
                                        initialValue: item.default_string,
                                        rules: [{ required: false, message: '请输入名称' }],
                                    },
                                ]" style="width: 280px" />
                            </a-input-group>
                        </a-form-item>

                        <a-form-item v-for="(choice, index) in choice_parameter" :key="'c' + index" :label="language.label">
                            <a-input-group>
                                <a-input style="width: 130px" v-model="choice.name" :disabled="true" />
                                <span style="
                                    width: 40px;
                                    float: left;
                                    text-align: center;
                                    line-height: 30px;
                                    border-bottom: 1px solid #ccc;
                                    border-top: 1px solid #ccc;
                                ">=</span>
                                <a-select v-decorator="[
                                    choice.name,
                                    {
                                        initialValue: choice.choices_string_list[0],
                                        rules: [{ required: false, message: '请输入名称' }],
                                    },
                                ]" style="width: 280px" optionFilterProp="label" showSearch>
                                    <a-select-option v-for="(choices_string, choices_string_index) in choice.choices_string_list" :value="choices_string" :key="choices_string_index" :label="choices_string">{{ choices_string }}</a-select-option>
                                </a-select>
                            </a-input-group>
                        </a-form-item>
                    </a-form>
                </a-spin>
            </a-modal>
            <a-modal v-model="deleteModel" @cancel="onCancel" @ok="onDeleteOk" :confirmLoading="deleteLoading">
                <h3 style="font-size: 18px">
                    <a-icon style="color: red" type="exclamation-circle" /> <span>{{language.deleteMessage1}}</span>
                </h3>
                <p>{{language.deleteMessage2}}【{{ selectDeleteObject.name }}】？</p>
                <a-form-item :label="language.deleteMessage3">
                    <a-input :placeholder="language.deleteMessage3" v-model="delete_name"></a-input>
                </a-form-item>
            </a-modal>
        </a-card>
    </div>
</template>

<script>
var moment = require('moment')
import { getAssemblyLine, delAssemblyLine, immediatelyAssemblyLine, stopExecution, deleteHistory, hasBuilding, jenkinsTags, syncApplicationPipelines, refreshJenkinsJobs } from '@/api/assemblyLine'
import { getBusinessTree } from '@/api/business.js'
import { getParameterSetting } from '@/api/reconfig.js'

import AddAssemblyLine from './model/addAssemblyLine.vue'

export default {
    data() {
        return {
            treeData: [{ title: "全部流水线", key: "all", children: [] }],
            tableData: [],
            tableLoading: false,
            tableQuery: {
                search_type: 'job_name',
                search_data: undefined,
                current: 1,
                pageSize: 10,
                total: 0,
            },
            // 树选中的项
            selectedKeys: [],
            expandedKeys: ["all"],
            showTree: false,
            spinning: false,

            // 立即执行确定按钮
            immediatelyConfirmLoading: false,
            // 立即执行弹框
            immediatelyModel: false,
            // 立即执行参数
            immediateExecutionList: [
                { key: '', value: '', disable: true },
                { key: '', value: '', disable: false },
            ],
            immediateForm: this.$form.createForm(this, { name: 'immediateForm' }),
            modalLoading: false,
            // 字符串型参数
            string_parameter: [],
            // 选择型参数
            choice_parameter: [],
            // 是否有流水线正在构建
            isBuilding: false,
            // 是否停止调取流水线数据
            isStop: false,
            // 是否停止循环请求接口
            destroy: false,

            selectObj: {}, //左侧选中的项
            selectType: "all",
            selectCode: "all",
            selectParams: {},

            deleteModel: false,
            selectDeleteObject: {},//操作删除的数据
            delete_name: "",
            deleteLoading: false,
        }
    },
    computed: {
        searchList() {
            return [
                { name: this.language.searchList1, key: 'job_name' },
                { name: this.language.searchList2, key: 'last_run_username' },
                { name: this.language.searchList3, key: 'description' },   
            ]
        },
        columns() {
            return [
                { title: this.language.columns1, dataIndex: 'name', scopedSlots: { customRender: 'name' }, width: 220, },
                { title: this.language.columns2, dataIndex: 'status', scopedSlots: { customRender: 'status' }, width: 120, },
                { title: this.language.columns3, dataIndex: 'last_run_number', scopedSlots: { customRender: 'last_run_number' }, width: 120, },
                { title: this.language.columns4, dataIndex: 'last_run_username', scopedSlots: { customRender: 'last_run_username' }, width: 110, ellipsis: true, },
                { title: this.language.columns5, dataIndex: 'last_run_req_source', customRender: text => text || "--", width: 110, ellipsis: true, },
                { title: this.language.columns6, dataIndex: 'show_last_run_datetime', width: 160, },
                { title: this.language.columns7, dataIndex: 'show_application', width: 150, ellipsis: true, },
                { title: this.language.columns8, scopedSlots: { customRender: 'action' }, fixed: "right", width: 120, align: "center", },
            ]
        }
    },
    created() {
        if (this.$route.query.current && this.$route.query.pageSize) {
            let query = this.$route.query
            this.tableQuery.current = query.current - 0
            this.tableQuery.pageSize = query.pageSize - 0
            this.tableQuery.search_type = query.search_type
            this.tableQuery.search_data = query.search_data
            //从详情页返回
            if (query.selectType) {
                if (query.selectType == "all") {
                    this.selectType = "all"
                    this.selectCode = query.selectCode
                    this.selectParams = { all_data: 1 }
                } else if (query.selectType == "BUSINESS") {
                    this.selectType = "BUSINESS"
                    this.selectCode = query.selectCode
                    this.selectParams = { business_code: this.selectCode }
                } else if (query.selectType == "APPLICATION") {
                    this.selectType = "APPLICATION"
                    this.selectCode = query.selectCode
                    this.selectParams = { code: this.selectCode }
                }
            }
        }
        this.language = Object.assign({}, this.$store.state.language.languageAuth.public1 || {}, this.$store.state.language.languageAuth.assemblyLine || {})
    },
    mounted() {
        this.getBusinessTreeData(true)
        // 打开新建弹框
        if (this.$route.query.isOpen == 1) {
            this.selectType = "APPLICATION"
            this.selectCode = this.$route.query.appCode
            this.selectParams = { application: this.$route.query.appCode }
            this.selectedKeys = [this.selectCode + ""]
            this.$refs.AddAssemblyLine.show(this.$route.query.appCode, { ...this.tableQuery, selectType: this.selectType, selectCode: this.selectCode })
        }
        if (this.$route.query.name && this.$route.query.search_type == "code") {
            this.tableQuery.search_data = this.$route.query.name
            this.selectType = "APPLICATION"
            this.selectCode = this.$route.query.appCode
            this.selectParams = { code: this.$route.query.appCode }
            this.selectedKeys = [this.selectCode + ""]

        } else {
            if (this.selectCode == "all") {
                this.selectParams = { all_data: 1 }
                this.selectedKeys = [this.selectCode + ""]

            } else if (this.selectType == "BUSINESS") {
                this.selectParams = { business_code: this.selectCode }
                this.selectedKeys = ["n" + this.selectCode]
            } else if (this.selectType == "APPLICATION") {
                this.selectParams = { code: this.selectCode }
                this.selectedKeys = [this.selectCode + ""]
            }
        }

        this.getTableData(true, true)
        setTimeout(() => {
            this.loop()
        }, 5000)
        this.$once('hook:beforeDestroy', () => {
            this.destroy = true
        })
    },
    methods: {
        routerGoto(record) {
            this.$router.push({ name: 'executionLogDefault', query: { appCode: record.application.code,...this.tableQuery,selectType:this.selectType,selectCode:this.selectCode, view_name:record.view_name,number: record.last_run_number, job_name: record.name, job_code:record.code,fromName:'myCollection' } })
        },
        // 循环调取流水线数据
        loop() {
            if (!this.destroy) {
                this.getTableData(null).then(res => {
                    setTimeout(() => {
                        if (!this.isStop && !this.destroy) {
                            this.loop()
                        }
                    }, 5000)
                })
            }
        },
        reload() {
            this.getTableData(true)
        },
        onSelect(val, info) {
            console.log(info.node)
            this.selectObj = info.node.dataRef
            this.selectedKeys = [info.node.eventKey]
            this.selectType = info.node.dataRef.type
            this.selectCode = info.node.dataRef.code || info.node.eventKey
            this.tableQuery.current = 1
            if (this.selectCode == "all") {
                this.selectParams = { all_data: 1 }
            } else if (this.selectType == "BUSINESS") {
                this.selectParams = { business_code: this.selectCode }
            } else if (this.selectType == "APPLICATION") {
                this.selectParams = { code: this.selectCode }
            }
            this.getTableData(true)
        },
        // 获取业务与应用(用于选择应用)
        getBusinessTreeData(first) {
            getBusinessTree().then((res) => {
                if (res.data) {
                    this.treeData[0].children = res.data.filter((item) => {
                        return item.children && item.children.length > 0
                    })
                    if (this.treeData[0].children == 0) {
                        this.tableLoading = false
                        return
                    }
                    let groupCode
                    let all_tags_job_count = 0
                    res.data.map((item) => {
                        item.key = 'n' + item.code
                        item.value = 'n' + item.code
                        item.title = item.name
                        let tags_job_count = 0
                        item.children.map((ele) => (tags_job_count += ele.tags_job_count || 0))
                        item.tags_job_count = tags_job_count
                        all_tags_job_count += tags_job_count
                        this.$set(item, 'scopedSlots', { title: 'title_name' })
                        item.children.map((ele) => {
                            if (first && this.$route.query.appCode) {
                                if (ele.code == this.$route.query.appCode) {
                                    groupCode = item.key
                                }
                            }
                            ele.key = ele.code + ''
                            ele.value = ele.code + ''
                            ele.title = ele.name
                            this.$set(ele, 'scopedSlots', { title: 'title_name' })
                        })
                    })
                    this.treeData[0].tags_job_count = all_tags_job_count
                    this.$set(this.treeData[0], 'scopedSlots', { title: 'title_name' })
                    if (first && this.$route.query.appCode) {
                        this.expandedKeys = [groupCode]
                    } else if (first) {
                    }

                    this.showTree = false
                    this.$nextTick(() => {
                        this.showTree = true
                    })
                }
            }).finally(() => {
                this.showTree = false
                this.$nextTick(() => {
                    this.showTree = true
                })
            })
        },
        getTableData(loading, first) {
            let updata = { ...this.tableQuery, ...this.selectParams, list_type: "tags" }

            let flag = false
            this.$once('hook:beforeDestroy', () => {
                this.destroy = true
                flag = true
            })
            if (loading) {
                this.tableLoading = true
            }
            return getAssemblyLine(updata)
                .then((res) => {
                    if (res.data.current > 1 && res.data.data.length == 0 && res.data.total > 0) {
                        this.tableQuery.current = 1
                        return this.getTableData(true)
                    }
                    if (res.data && res.data.data) {
                        this.tableQuery.total = res.data.total
                        this.tableData = res.data.data
                        res.data.data.forEach(item => {
                            this.$set(item, "btnLoading", false)
                            item.last_run_number = item.build?.number
                            item.last_run_username = item.build?.username
                            item.last_run_req_source = item.build?.req_source
                            item.last_run_datetime = item.build?.datetime
                            item.status = item.build?.result

                            item.show_last_run_datetime = item.last_run_datetime && moment(item.last_run_datetime).format("YYYY-MM-DD HH:mm:ss") || "--"
                            item.show_application = item.application?.visible_name || "--"
                        })
                        if (this.$route.query.isRun && this.$route.query.code && first) {
                            let obj = res.data.data.find(item => {
                                return item.code == this.$route.query.code
                            })
                            this.immediatelyHandle(obj)
                        }
                    } else {
                        this.tableData = []
                    }
                })
                .catch((res) => {
                    this.isStop = true
                    if (res.code == 404 && res.errcode == 40401) {
                        this.noJenkins = true
                    } else {
                        this.$message.error(res.message)
                    }
                })
                .finally((res) => {
                    this.tableLoading = false
                })
        },
        tableChange({ current, pageSize }) {
            this.tableQuery.current = current
            this.tableQuery.pageSize = pageSize
            this.getTableData(true)
        },
        // 立即执行事件
        immediatelyHandle(record) {
            this.string_parameter = []
            this.choice_parameter = []
            this.activeJob = record
            record.btnLoading = true
            getParameterSetting({ code: record.application.code, job_name: record.name }).then((res) => {
                // this.$message.info("正在获取参数")
                if (
                    (res.code == 200 && res.data && res.data.string_parameter.length > 0) ||
                    res.data.choice_parameter.length > 0
                ) {
                    this.string_parameter = res.data.string_parameter
                    this.choice_parameter = res.data.choice_parameter
                    this.immediatelyModel = true
                } else {
                    let _this = this
                    this.$confirm({
                        title: `确认执行【${record.name}】流水线吗?`,
                        onOk: () => {
                            return new Promise((resolve, reject) => {
                                _this.immediatelyHandleOk().then(res => {
                                    resolve()
                                }).finally(() => {
                                    reject()
                                })
                            })
                        },
                    })
                }
            }).finally(() => {
                record.btnLoading = false
            })
        },
        // 立即执行
        immediatelyHandleOk() {
            this.active = this.activeJob
            let parameters
            this.immediateForm.validateFields((err, values) => {
                parameters = values
            })
            this.immediatelyConfirmLoading = true
            return immediatelyAssemblyLine({
                code: this.active.application.code,
                name: this.active.name,
                parameters,
            })
                .then((res) => {
                    if (res.code == 200) {
                        this.$message.success(res.message)
                        this.immediatelyModel = false
                        this.getTableData(true)
                    } else {
                        this.$message.error(res.message)
                    }
                })
                .finally(() => {
                    this.immediatelyConfirmLoading = false
                })
        },
        // 收藏
        collect(record) {
            record.btnLoading = true
            jenkinsTags({ code: record.application.code, job_code: record.code, tags: !record.tags })
                .then((res) => {
                    if (res.code == 200) {
                        this.getTableData(null)
                    }
                })
                .catch(() => {
                }).finally(() => {
                    record.btnLoading = false
                })
        },
        // 取消删除
        onCancel() {
            this.deleteModel = false
            this.delete_name = ''
            this.selectDeleteObject = {}
        },
        // 确认删除
        onDeleteOk() {
            if (this.delete_name == this.selectDeleteObject.name) {
                this.deleteLoading = true
                delAssemblyLine({
                    code: this.selectDeleteObject.application.code,
                    name: this.selectDeleteObject.name,
                }).then((res) => {
                    if (res.code == 200) {
                        this.$message.success(res.message)
                        this.getTableData(true)
                        this.getBusinessTreeData()
                        this.onCancel()
                    } else {
                        this.$message.error(res.message)
                    }
                }).finally(() => {
                    this.deleteLoading = false
                })

            } else {
                return this.$message.warning("请输入正确的流水线名称")
            }
        },
        // 删除流水线
        deleteAssemblyLine(record) {
            this.deleteModel = true
            this.selectDeleteObject = record
        },
        // 搜索
        searchTable() {
            this.tableQuery.current = 1
            this.getTableData(true)
        },
    },
    components: {
        AddAssemblyLine,
    }
}
</script>

<style lang="less" scoped>
.content {
	display: flex;
	.content_left {
		// flex: 0 0 260px;
		min-width: 210px;
		flex: 260 260 0px;
		overflow: hidden;
		padding: 0px 15px 0px 0;
		border-right: 1px solid #e8e8e8;
		/deep/.ant-tree li .ant-tree-node-content-wrapper {
			max-width: calc(100% - 20px);
			overflow: hidden;
			display: inline-block;
			text-overflow: ellipsis;
		}
	}
	.content_right {
		// flex: 1 1 300px;
		flex: 1400 1400 0px;
		overflow: hidden;
		padding: 0px 0px 0px 15px;
	}
}
.top_search {
	margin: 0 0 10px 0;
}
.color_box {
	i {
		margin: 0 5px 0 0;
	}
}
.action_icon {
	color: @primary-color;
	cursor: pointer;
}
.ellipsis_dom {
	overflow: hidden;
	white-space: nowrap;
	width: 100%;
	text-overflow: ellipsis;
	display: block;
}
.action_box {
	display: flex;
	.action_box_right {
		position: absolute;
		right: -10px;
		min-width: 30px;
		background-color: #ffffff;
	}
	.tree_tag {
		background-color: #e7f6ef;
		color: #52c1d8;
		border: none;
		margin: 0 10px;
	}
}
.action_icon_hover {
	color: #666;
	cursor: pointer;
	&:hover {
		color: @primary-color;
	}
}
</style>
