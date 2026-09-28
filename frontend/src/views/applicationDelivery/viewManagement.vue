<template>
    <div>
        <content-header>
            <div slot="docs">用户可以创建跨应用系统的全局视图，可以基于环境、前后端等维度进行流水线分组。</div>
        </content-header>
        <a-card>
            <div class="content">
                <div v-show="!(allHomePageTabList.length == 0 && isOver)" class="content_header">
                    <div class="tab_box">
                        <div @click="scrollLeft" class="arrow_box" :style="{ display: showArrow ? 'block' : 'none' }">
                            <a-icon type="left"></a-icon>
                        </div>
                        <div class="content_header_tab" ref="tabRollBox">
                            <a-spin :spinning="homePageTabLoading" class="tab_spin">
                                <!-- 按钮注意权限控制 -->
                                <draggable v-model="homePageTabList" :animation="200" style="display: flex;" handle=".drag_icon" @change="dragHomePageTab">
                                    <div v-for="item in homePageTabList" :key="item.code" class="content_header_tab_item" :class="{ content_header_tab_item_active: item.code == activeTab }" @click="
									() => {
										activeTab = item.code;
										getTableData(item.code);
									}
								">
                                        <span>
                                            <div class="drag_icon">
                                                <a-tooltip title="按住此区域可拖动排序">
                                                    <a-icon type="drag"></a-icon>
                                                </a-tooltip>
                                            </div>
                                            <span>{{ item.overall_view_name }}</span>
                                            <div class="edit_icon" v-if="(item.overall_view_type == '1' && $store.state.btnAuth.btnAuth.pipeline_overall_public_view_update) || (item.overall_view_type == '2' && item.can_update)">
                                                <a-tooltip title="编辑视图">
                                                    <a-icon style="margin:0 3px 0 0;" type="edit" @click.stop.native="$refs.AddView.onShow(item)"></a-icon>
                                                </a-tooltip>
                                            </div>
                                        </span>
                                    </div>
                                </draggable>
                                <a-popover v-model="isShow" trigger="click" placement="bottomRight" overlayClassName="custom_popover">
                                    <div slot="content" class="panel_content">
                                        <a-spin :spinning="tabLoading" class="custom_spin">
                                            <div class="panel_content_title">
                                                <strong> 管理视图</strong>
                                                <div style="padding:5px 0">
                                                    <a-button v-if="$store.state.btnAuth.btnAuth.pipeline_overall_view_create" size="small" type="link" style="margin-left:10px" @click="$refs.AddView.onShow();isShow = false">
                                                        <a-icon type="plus-circle"></a-icon>
                                                        <span>新建视图</span>
                                                    </a-button>
                                                </div>
                                            </div>
                                            <div class="setting_panel">
                                                <template v-for="group in tabList">
                                                    <div v-if="group.children && group.children.length" class="group">
                                                        <div class="group_title">
                                                            <span class="group_title_name">{{ group.group_name }}</span>
                                                            <span class="group_title_desc">{{ group.description }}</span>
                                                        </div>
                                                        <div v-for="item in group.children" class="setting_panel_item">
                                                            <div class="setting_panel_item_left">
                                                                <div class="title">
                                                                    <span class="name">{{ item.overall_view_name }}</span>
                                                                    <span class="tag">{{ item.overall_view_type == '1' ? "公共" : "私有" }}</span>
                                                                    <a-tooltip title="编辑视图" v-if="(item.overall_view_type == '1' && $store.state.btnAuth.btnAuth.pipeline_overall_public_view_update) || (item.overall_view_type == '2' && item.can_update)">
                                                                        <a-icon type="edit" class="edit_icon" @click.stop.native="$refs.AddView.onShow(item);isShow = false"></a-icon>
                                                                    </a-tooltip>
                                                                    <a-tooltip title="删除视图" v-if="(item.overall_view_type == '1' && $store.state.btnAuth.btnAuth.pipeline_overall_public_view_delete) || (item.overall_view_type == '2' && item.can_update)">
                                                                        <a-icon type="delete" class="edit_icon" @click.stop.native="deleteView(item);isShow = false"></a-icon>
                                                                    </a-tooltip>
                                                                </div>
                                                                <div class="desc" :title="item.overall_view_describe">{{ item.overall_view_describe || "暂无描述" }}</div>
                                                            </div>
                                                            <div class="setting_panel_item_right" :title="
														tabList.reduce((pre, cur) => [...pre, ...cur.children], []).filter(i => i.bind).length == 1 &&
														item.bind
															? undefined
															: '选择是否开启此视图'
													">
                                                                <a-tooltip :title="
															tabList.reduce((pre, cur) => [...pre, ...cur.children], []).filter(i => i.bind).length ==
																1 && item.bind
																? '至少开启一个视图'
																: undefined
														">
                                                                    <a-switch checked-children="开" un-checked-children="关" @change="val => handleChangeBind(item, val)" :checked="item.bind" :loading="item.bindLoading" :disabled="
																tabList.reduce((pre, cur) => [...pre, ...cur.children], []).filter(i => i.bind)
																	.length == 1 && item.bind
															"></a-switch>
                                                                </a-tooltip>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </template>
                                            </div>
                                        </a-spin>
                                    </div>
                                    <a-tooltip title="管理视图">
                                        <div class="setting_icon">
                                            <a-icon type="setting"></a-icon>
                                        </div>
                                    </a-tooltip>
                                </a-popover>
                            </a-spin>
                        </div>
                        <div @click="scrollRight" class="arrow_box" :style="{ display: showArrow ? 'block' : 'none' }">
                            <a-icon type="right"></a-icon>
                        </div>
                    </div>
                </div>
                <div v-show="!(allHomePageTabList.length == 0 && isOver)">
                    <div class="top_search">
                      
                            <a-input-search v-model="tableQuery.search_data" @search="searchTable" :placeholder="language.search_placeholder" style="width: 300px;margin:0 10px 0 0" allowClear>
                                <a-select slot="addonBefore" style="width: 100px" v-model="tableQuery.search_type">
                                    <a-select-option v-for="item in searchList" :value="item.key" :key="item.key">{{ item.name }}</a-select-option>
                                </a-select>
                            </a-input-search>

                            <span style="line-height:30px;">所属应用：</span>
                            <a-select v-model="tableQuery.application_code" @change="searchTable" allowClear placeholder="请选择所属应用" style="width:200px;">
                                <a-select-opt-group v-for="item in applicationList" :key="item.code">
                                    <span slot="label">{{item.name}}</span>
                                    <a-select-option v-for="ele in item.children" :value="ele.code" :key="ele.code">
                                        {{ele.name}}
                                    </a-select-option>
                                </a-select-opt-group>
                            </a-select>

                        <a-button :loading="tableLoading" @click="reload" icon="reload" style="float: right">刷新</a-button>
                    </div>
                    <a-table :row-key="(record) => record.code" @change="tableChange" :loading="{spinning:tableLoading,tip:'正在加载中，请耐心等待...'}" :columns="columns" :dataSource="tableData" :pagination="{...tableQuery,showSizeChanger: true,showTotal: (total) => `共 ${total} 条数据`,showQuickJumper: true,
                        pageSizeOptions: ['10','20','40','50','100','150','200',],}" :scroll="{x:1000}">
                        <template slot="name" slot-scope="text, record">
                            <a v-if="record.can_log" :title="text" @click="$router.push({name:'executionLog',query:{appCode:record.application.code,job_name:record.name,...tableQuery,view_name:record.view_name,job_code:record.code,activeTab:activeTab,fromName:'viewManagement'}})">{{text}}</a>
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
                                        <a-menu-item v-if="record.can_update" @click="$router.push({path: '/applicationDelivery/assemblyLine/pipelineConfiguration',query: {name:record.name,appCode: record.application.code,...tableQuery,view_name:record.view_name,activeTab:activeTab,fromName:'viewManagement'},})">
                                            {{language.edit}}
                                        </a-menu-item>
                                        <a-menu-item v-if="record.can_log" @click="$router.push({name:'executionLog',query:{appCode:record.application.code,job_name:record.name,...tableQuery,view_name:record.view_name,job_code:record.code,activeTab:activeTab,fromName:'viewManagement'}})">
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
                <a-modal v-model="deleteModel" @cancel="onCancel" @ok="onDeleteOk" okType="danger" :confirmLoading="deleteLoading">
                    <h3 style="font-size: 18px;color: red">
                        <a-icon type="exclamation-circle" /> <span>{{language.deleteMessage1}}</span>
                    </h3>
                    <p>{{language.deleteMessage2}}【{{ selectDeleteObject.name }}】？</p>
                    <a-form-item :label="language.deleteMessage3">
                        <a-input :placeholder="language.deleteMessage3" v-model="delete_name"></a-input>
                    </a-form-item>
                </a-modal>
            </div>
            <div v-show="allHomePageTabList.length == 0 && isOver">
                <a-empty style="margin:60px 0 80px 0;">
                    <div slot="description">
                        <h3>欢迎使用视图管理功能</h3>
                        <p>当流水线数据过多，不易查看使用时，可以创建不同维度的视图去管理流水线数据。</p>
                        <a-button v-if="$store.state.btnAuth.btnAuth.pipeline_overall_view_create" @click="$refs.AddView.onShow()" icon="plus" type="primary">创建视图</a-button>
                        <a-tooltip v-else title="提示：暂无此权限，请联系管理员授权。">
                            <a-button disabled icon="plus" type="primary">创建视图</a-button>
                        </a-tooltip>
                    </div>
                </a-empty>
                <div>
                    <div class="descrip_row">
                        <div class="box">
                            <h3>创建视图</h3>
                            <p>点击创建视图按钮，会打开创建视图的抽屉页面，用户可以自定义创建视图的名称、权限范围、描述、以及关联的流水线等数据。</p>
                        </div>
                        <a-icon style="font-size:20px;margin:0 30px;color:#ccc" type="arrow-right" />
                        <div class="box">
                            <h3>从不同维度的视图管理流水线</h3>
                            <p>视图创建完成后，会以标签页的方式展示，切换不同的视图标签页可以查看以及管理对应视图的流水线数据。</p>
                        </div>
                    </div>
                </div>
            </div>
        </a-card>
        <AddView @ref-list="getOverview(),getTemplateConfig()" ref="AddView"></AddView>
        <!-- 构建详情 -->
    </div>
</template>

<script>
var moment = require('moment')
import { GridLayout, GridItem } from "vue-grid-layout";
import { readDirfiles, triggerWindowResizeEvent } from "@/utils/util";
// import { getTemplateConfig, changeTemplateConfig, getOuterPanelShow, editOuterPanelShow } from "@/api/homeData.js";
import { changeTemplateConfig, getJenkinsViews as getOuterPanelShow, getTemplateConfig, deleteJenkinsViews } from "@/api/view.js"
import { getAssemblyLine, delAssemblyLine, immediatelyAssemblyLine, stopExecution, deleteHistory, hasBuilding, jenkinsTags, syncApplicationPipelines, refreshJenkinsJobs } from '@/api/assemblyLine'
import { getParameterSetting } from '@/api/reconfig.js'
import { getBusinessTree } from '@/api/business.js'

import draggable from "vuedraggable";
import { debounce, flatten } from "lodash";
import AddView from "./components/addView.vue"
export default {
    components: { GridLayout, GridItem, draggable, AddView },
    data() {
        return {
            url: window.API_ROOT.replace("/workbench", ""),
            layout: [],
            draggable: false,
            resizable: false,
            loading: false,
            activeTab: undefined, //可以根据此标识来做权限 1为总览 2为运维管理
            tabList: [],
            showArrow: false,
            tabLoading: false,
            allHomePageTabList: [],
            homePageTabList: [],
            homePageTabLoading: false,
            tableData: [],
            tableLoading: false,
            tableQuery: {
                search_type: 'job_name',
                search_data: undefined,
                current: 1,
                pageSize: 10,
                total: 0,
                application_code: undefined,
            },

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

            deleteModel: false,
            selectDeleteObject: {},//操作删除的数据
            delete_name: "",
            deleteLoading: false,
            isOver: false,

            applicationList: [],
            isShow: false,
        };
    },
    methods: {
        routerGoto(record) {
            this.$router.push({ name: 'executionLogDefault', query: { appCode: record.application.code,...this.tableQuery, number: record.last_run_number, job_name: record.name,job_code:record.code,activeTab:this.activeTab,fromName:'viewManagement' } })
        },
        // 获取业务与应用(用于选择应用)
        getBusinessTreeData(first) {
            this.leftLoading = true
            return getBusinessTree().then((res) => {
                this.applicationList = res.data
            }).finally(() => {
                this.leftLoading = false
            })
        },
        reload() {
            this.getTableData(true)
        },
        // 搜索
        searchTable() {
            this.tableQuery.current = 1
            this.getTableData(true)
        },
        // 删除
        deleteView(record) {
            this.$confirm({
                content: "确认删除该视图吗？",
                okType: "danger",
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        deleteJenkinsViews({ code: record.code, }).then(
                            (res) => {
                                if (res.code == 200) {
                                    this.$message.success(res.message)
                                    if (record.code == this.activeTab) {
                                        this.activeTab = undefined
                                    }
                                    // 视图管理-删除视图后先调取视图管理接口然后调取视图tablist接口(配合后端存在多个视图且只有一个打开被删除后自动打开一个视图功能)
                                    this.getTemplateConfig().then(res =>{
                                        this.getOverview()
                                    })
                                    resolve()
                                } else {
                                    this.$message.error(res.message)
                                }
                            }
                        ).finally(() => {
                            reject()
                        })
                    })
                },
            })
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
        //获取头部tabList
        getOverview(first) {
            this.homePageTabLoading = true;
            getOuterPanelShow()
                .then(res => {
                    this.homePageTabList = res.data;
                })
                .finally(() => {
                    this.homePageTabLoading = false;
                    this.loading = false;
                    if (!this.activeTab) {
                        this.activeTab = this.homePageTabList[0]?.code;
                    }
                    if (this.activeTab) {
                        this.getTableData(this.activeTab);
                        setTimeout(() => {
                            this.loop()
                        }, 5000)
                    } else {
                        this.tableData = []
                    }
                });
        },
        // 获取视图详情数据
        getTableData(loading) {
            if (!this.activeTab) return;
            this.loading = true;
            let params = {
                overall_view_code: this.activeTab,
                ...this.tableQuery
            }
            let flag = false
            this.$once('hook:beforeDestroy', () => {
                this.destroy = true
                flag = true
            })
            if (loading) {
                this.tableLoading = true
            }
            return getOuterPanelShow(params).then((res) => {
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
                } else {
                    this.tableData = []
                }
            }).catch(() =>{
                this.isStop = true
            }).finally(() => {
                this.loading = false;
                this.tableLoading = false
            });
        },
        tableChange({ current, pageSize }) {
            this.tableQuery.current = current
            this.tableQuery.pageSize = pageSize
            this.getTableData(true)
        },
        getTemplateConfig() {
            this.tabLoading = true;
            return getTemplateConfig()
                .then(res => {
                    let arr = []
                    this.tabList = res.data;
                    this.tabList.forEach(item => {
                        item.children.forEach(i => {
                            this.$set(i, "bindLoading", false);
                            arr.push(i)
                        });
                    });
                    this.allHomePageTabList = arr
                })
                .finally(() => {
                    this.isOver = true
                    this.checkArrows();
                    this.tabLoading = false;
                });
        },
        // 开关
        handleChangeBind(item, val) {
            const params = {
                data_type: "enable",
                code: item.code,
            };
            item.bindLoading = true;
            changeTemplateConfig(params)
                .then(res => {
                    if (item.code == this.activeTab) {
                        this.activeTab = undefined
                    }
                    this.getTemplateConfig();
                    this.getOverview();
                })
                .finally(() => {
                    item.bindLoading = false;
                });
        },
        dragHomePageTab() {
            const ids = this.homePageTabList.map(item => item.code);
            changeTemplateConfig({ data_type: "index", overall_view_list: ids });
        },
        scrollLeft() {
            this.$refs.tabRollBox.scrollTo({ left: this.$refs.tabRollBox.scrollLeft - 350, behavior: "smooth" });
            this.checkArrows();
        },
        scrollRight() {
            this.$refs.tabRollBox.scrollTo({ left: this.$refs.tabRollBox.scrollLeft + 350, behavior: "smooth" });
            this.checkArrows();
        },
        checkArrows() {
            const tabRollBox = this.$refs.tabRollBox;
            this.showArrow = tabRollBox.scrollWidth > tabRollBox.clientWidth;
        },
        handleResize: debounce(function () {
            this.checkArrows();
        }, 300),
        destroyResize() {
            window.removeEventListener("resize", this.handleResize);
        },

        //监听窗口变化
        windowResize() {
            window.addEventListener("resize", this.handleResize);
            this.$on("hook:beforeDestroy", this.destroyResize);
        },
    },
    created() {
        let query = this.$route.query
        if (this.$route.query.current && this.$route.query.pageSize) {
            this.tableQuery.current = query.current - 0
            this.tableQuery.pageSize = query.pageSize - 0
            this.tableQuery.search_type = query.search_type
            this.tableQuery.search_data = query.search_data
            this.tableQuery.application_code = query.application_code
        }
        if(query.activeTab) {
            this.activeTab = query.activeTab || undefined
        }
        this.language = Object.assign({}, this.$store.state.language.languageAuth.public1 || {}, this.$store.state.language.languageAuth.assemblyLine || {})
    },
    mounted() {
        this.loading = true;
        this.homePageTabLoading = true
        if (this.$route.query.bind == '1') {
            this.activeTab = this.$route.query.id || undefined;
        }
        this.windowResize();
        this.getTemplateConfig().then(res =>{
            this.getOverview(true)
        })
        this.getBusinessTreeData()
        this.$once('hook:beforeDestroy', () => {
            this.destroy = true
        })
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
};
</script>

<style scoped lang="less">
.content {
	/deep/ .vue-grid-item {
		border: 1px solid transparent;
		background: #fff;
		overflow-y: auto;
		overflow-x: hidden;
		.delete_img {
			position: absolute;
			top: 5px;
			right: 5px;
			opacity: 0;
			transition: all 0.3s;
			cursor: pointer;
			font-size: 20px;
			color: @primary-color;
		}
		&:hover {
			border: 1px solid transparent;
			.delete_img {
				opacity: 1;
			}
		}
	}
	/deep/.vue-grid-item.vue-grid-placeholder {
		background: #0ba360;
	}
	&_header {
		display: flex;
		justify-content: space-between;
		background-color: #ffffff;
		margin: -14px 0px 20px 0px;
		min-height: 44px;
		align-items: center;
		box-sizing: border-box;
		border-bottom: 1px solid #e8e8e8;
		.tab_box {
			display: flex;
			align-items: center;
			flex: 1;
			overflow: hidden;
            margin:0 0 -1px 0;
			.arrow_box {
				line-height: 44px;
				cursor: pointer;
				padding: 0 10px;
				&:hover {
					background-color: #f0f2f5;
				}
			}
		}
		&_tab {
			width: 100%;
			display: flex;
			overflow: hidden;
			&_item {
				cursor: pointer;
				width: max-content;
				min-width: 120px;
				text-align: center;
				height: 40px;
				line-height: 40px;
				border: 1px solid #e8e8e8;
				border-radius: 4px;
				border-bottom-left-radius: 0;
				border-bottom-right-radius: 0;
				// border-bottom: none;
				padding: 0 45px;
				margin: 4px 4px 0 4px;
				position: relative;
				z-index: 1;
                background-color: #F6F6F6;
				.drag_icon {
					padding: 0 10px;
					position: absolute;
					left: -2px;
					top: 50%;
					transform: translateY(-50%);
					opacity: 0;
					z-index: 2;
					transition: all 0.3s;
					cursor: move;
					color: gray;
				}
				.edit_icon {
					padding: 0 10px;
					position: absolute;
					right: -2px;
					top: 53%;
					transform: translateY(-50%);
					opacity: 0;
					transition: all 0.3s;
					color: gray;
					&:hover {
						color: @primary-color;
					}
				}
				&:nth-of-type(1) {
					margin-left: 0px;
				}
				&:hover {
					.edit_icon {
						right: 0px;
						top: 53%;
						transform: translateY(-50%);
						opacity: 1;
					}
					.drag_icon {
						left: 0;
						top: 50%;
						opacity: 1;
					}
				}
			}
			&_item_active {
				// background-color: #f0f2f5;
				background-color: #fff;
				color: @primary-color;
                border-bottom: none;
			}
			.setting_icon {
				cursor: pointer;
				padding: 0 10px;
				line-height: 40px;
				margin: 4px 4px 0 4px;
				color: gray;
				&:hover {
					color: @primary-color;
				}
			}
		}
	}
}
/deep/ .tab_spin {
	width: 100%;
	.ant-spin-container {
		width: 100%;
		display: flex;
	}
}
.panel_content {
	// overflow-y: auto;
	// position: relative;
	&_title {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-bottom: 10px;
		strong {
			font-size: 16px;
			font-weight: bold;
		}
		div {
		}
	}
	.setting_panel {
		max-height: 500px;
		overflow-y: auto;
		&::-webkit-scrollbar {
			width: 5px;
			height: 110px;
			background-color: transparent;
		}
		/*定义滚动条轨道 内阴影+圆角*/
		&::-webkit-scrollbar-track {
			border-radius: 10px;
			background-color: transparent;
		}
		/*定义滑块 内阴影+圆角*/
		&::-webkit-scrollbar-thumb {
			border-radius: 10px;
			background-color: #bdbdbd;
		}
		/*滑块效果*/
		&::-webkit-scrollbar-thumb:hover {
			border-radius: 5px;
			background: rgba(0, 0, 0, 0.4);
		}
		.group {
			padding: 0 10px;
			&_title {
				border-bottom: 1px solid #eeeeee;
				padding: 10px 0 8px 0;
				&_name {
					color: #333;
				}
				&_desc {
					font-size: 12px;
					padding-left: 8px;
					color: #888;
				}
			}
		}

		&_item {
			width: 400px;
			display: flex;
			padding: 10px;
			margin: 10px 0;
			align-items: center;
			justify-content: space-between;
			background: #f5f7f9;
			overflow: hidden;
			&:hover {
				.setting_panel_item_left {
					.title {
						.edit_icon {
							display: initial;
							color: @primary-color;
						}
					}
				}
			}
			&_left {
				flex: 1;
				overflow: hidden;
				margin-right: 10px;
				.title {
					font-size: 14px;
					color: #333;
					overflow: hidden;
					white-space: nowrap;
					text-overflow: ellipsis;
					display: flex;
					justify-items: flex-start;
					align-items: center;
					.name {
						overflow: hidden;
						white-space: nowrap;
						text-overflow: ellipsis;
					}
					.tag {
						font-size: 12px;
						padding: 0 4px;
						background-color: fade(@primary-color, 10%);
						color: @primary-color;
						border-radius: 2px;
						margin-left: 6px;
					}
					.edit_icon {
						cursor: pointer;
						margin: 0 5px;
						display: none;
						color: @primary-color;
					}
				}
				.desc {
					font-size: 12px;
					color: #999;
					margin-top: 4px;
					overflow: hidden;
					white-space: nowrap;
					text-overflow: ellipsis;
				}
			}
			&:nth-child(1) {
				margin-top: 0;
			}
		}
	}
}

/deep/ .ant-alert-info {
	background: #ffffff;
	border-color: #eeeeee;
	font-size: 13px;
	padding: 4.5px 15px 4.5px 37px;
}
/deep/ .ant-alert-icon {
	top: 5px;
}
.topbtn_rightbox {
	display: flex;
	align-items: center;
	&_content {
		display: flex;
		align-items: center;
		margin-left: 20px;
		cursor: pointer;
		color: #000000a6;
		.icon {
			padding-top: 2px;
			padding-right: 3px;
		}
		&:hover {
			color: @primary-color;
		}
	}
}
.radio_btn {
	.radio_btn_box {
		min-width: 90px;
		text-align: center;
		position: relative;
		z-index: 1;
		.edit_icon {
			padding: 10px;
			position: absolute;
			right: -30px;
			top: 50%;
			transform: translateY(-50%);
			opacity: 0;
			transition: all 0.3s;
		}
	}
	&:hover {
		.edit_icon {
			right: -14px;
			top: 50%;
			transform: translateY(-50%);
			opacity: 1;
		}
	}
}
.custom_spin {
	.ant-spin-container {
		position: relative;
		z-index: 2;
	}
}
.descrip_row {
	display: flex;
	align-items: center;
	justify-content: center;
	margin: 0 0 60px 0;
	.box {
		width: 280px;
		padding: 20px;
		box-shadow: 0 2px 12px 0 rgba(9, 21, 48, 0.12);
		height: 200px;
		h3 {
			text-align: center;
			font-weight: 1000;
			margin: 10px 0 20px 0;
		}
	}
}
</style>


<style lang="less" scoped>
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

