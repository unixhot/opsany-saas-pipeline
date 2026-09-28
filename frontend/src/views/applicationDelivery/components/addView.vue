<template>
    <div>
        <a-drawer :bodyStyle="{paddingBottom:'50px'}" width="1000px" :title="title" @close="onClose" :visible="visible" :destroyOnClose="true">
            <a-spin :spinning="spinning">
                <a-form-model ref="ruleForm" :model="formData" :rules="rules">
                    <a-form-model-item label="视图名称" prop="overall_view_name">
                        <a-input v-model="formData.overall_view_name" placeholder="请输入视图名称"></a-input>
                    </a-form-model-item>
                    <a-form-model-item label="视图权限" prop="overall_view_type">
                        <a-radio-group v-model="formData.overall_view_type">
                            <a-radio v-if="($store.state.btnAuth.btnAuth.pipeline_overall_public_view_create && !isEdit) || ($store.state.btnAuth.btnAuth.pipeline_overall_public_view_update && isEdit) " value="1">公开</a-radio>
                            <a-tooltip v-else title="提示：暂无此权限，请联系管理员授权。">
                                <a-radio value="1" disabled>公开</a-radio>
                            </a-tooltip>
                            <a-radio v-if="($store.state.btnAuth.btnAuth.pipeline_overall_private_view_create && !isEdit) || isEdit" value="2">私有</a-radio>
                            <a-tooltip v-else title="提示：暂无此权限，请联系管理员授权。">
                                <a-radio value="2" disabled>私有</a-radio>
                            </a-tooltip>
                        </a-radio-group>
                    </a-form-model-item>
                    <a-form-model-item label="描述" prop="overall_view_describe">
                        <a-textarea v-model="formData.overall_view_describe" :rows="4" placeholder="请输入描述"></a-textarea>
                    </a-form-model-item>
                    <a-form-model-item label="选择视图关联的流水线" class="ant-form-item-required">
                        <div class="box_content">
                            <div class="box_content_left">
                                <a-spin :spinning="leftLoading">
                                    <a-tree @select="treeSelect" :treeData="treeData" :selectedKeys="treeSelectedKeys" :show-line="false" :defaultExpandAll="true" :show-icon="false">
                                        <span slot="title_name" slot-scope="record" :title="`${record.title}`">
                                            <span class="app_title">{{record.title}}</span>
                                            <span class="app_number">({{record.job_count}})</span>
                                        </span>
                                    </a-tree>
                                </a-spin>
                            </div>
                            <div class="box_content_right">
                                <div class="top_search" style="margin:0 0 10px 0;">
                                    <a-input-search v-model="tableQuery.search_data" @search="searchTable" placeholder="请输入关键字搜索" style="width: 320px" allowClear>
                                        <a-select slot="addonBefore" style="width: 110px" v-model="tableQuery.search_type">
                                            <a-select-option :title="item.name" v-for="item in searchList" :key="item.key">{{ item.name }}</a-select-option>
                                        </a-select>
                                    </a-input-search>
                                </div>
                                <a-table :row-key="(record) => record.code" :loading="{spinning:tableLoading,tip:'正在加载中，请耐心等待...'}" :columns="columns" :dataSource="tableData" :pagination="false" :scroll="{y:400}" :row-selection="rowSelection">
                                    <template slot="job_name" slot-scope="text,record">
                                        <p class="ellipsis_row" style="color:#333;" :title="text">{{text}}</p>
                                        <p class="ellipsis_row" style="font-size:12px;" :title="record.description">{{record.description || "--"}}</p>
                                    </template>
                                </a-table>
                            </div>
                        </div>
                    </a-form-model-item>
                </a-form-model>
            </a-spin>
            <footer>
                <a-button @click="onOk" :loading="btnLoading" type="primary">确定</a-button>
                <a-button @click="onClose">取消</a-button>
            </footer>
        </a-drawer>
    </div>
</template>

<script>
import moment from 'moment'
import { addJenkinsViews, editJenkinsViews, getOverallView } from "@/api/view.js"
import { getBusinessTree } from '@/api/business.js'
import { getAllJenkins } from "@/api/view.js"
import cloneDeep from 'lodash.clonedeep'
export default {
    data() {
        return {
            // overall_view_type 1公开 2私有
            visible: false,
            title: "新增视图",
            formData: {
                overall_view_name: "",
                overall_view_type: "",
                overall_view_describe: "",
            },
            rules: {
                overall_view_name: [{ required: true, message: "请输入视图名称", whitespace: true, }, { max: 50, message: "视图名称长度限制在50个字符以内" }],
                overall_view_type: [{ required: true, message: "请选择视图权限", }],
                overall_view_describe: [{ max: 200, message: "描述长度限制在200个字符以内" }],
            },
            btnLoading: false,
            tableData: [],
            columns: [
                { title: '名称', dataIndex: 'job_name', scopedSlots: { customRender: 'job_name' }, ellipsis: true, },
            ],
            tableLoading: false,
            btnLoading1: false,
            //全部服务
            allTableData: [],
            selectedRowKeys: [],
            oldSelectedRowKeys: [],
            isEdit: false,
            treeData: [
                { title: "所有流水线", name: "所有流水线", key: "all", children: [], scopedSlots: { title: 'title_name' }, }
            ],
            treeSelectedKeys: ["all"],
            tableQuery: {
                search_type: 'job_name',
                search_data: undefined,
            },
            searchList: [{ key: "job_name", name: "流水线名称" }, { key: "description", name: "描述" }],
            leftLoading: false,
            spinning: false,
        }
    },
    computed: {
        rowSelection() {
            return {
                selectedRowKeys: this.selectedRowKeys,
                onChange: (selectedRowKeys, selectedRows) => {
                    this.selectedRowKeys = selectedRowKeys
                },
            }
        },
    },
    methods: {
        searchTable() {
            this.tableData = this.allTableData.filter(item => {
                return item[this.tableQuery.search_type].toUpperCase().indexOf(this.tableQuery.search_data.toUpperCase()) > -1
            })
        },
        getTableData() {
            this.tableLoading = true
            return getAllJenkins()
                .then((res) => {
                    this.allTableData = res.data
                    this.tableData = this.allTableData
                })
                .catch((res) => {

                })
                .finally((res) => {
                    this.tableLoading = false
                })
        },
        // 获取业务与应用(用于选择应用)
        getBusinessTreeData(first) {
            this.leftLoading = true
            return getBusinessTree().then((res) => {
                this.treeData[0].children = res.data.filter(item => {
                    return item.children.length > 0
                })
                res.data.map((item) => {
                    item.key = "n-" + item.unique_code
                    item.title = item.name
                    item.jobNumber = 0
                    this.$set(item, 'scopedSlots', { title: 'title_name' })
                    this.$set(item, "checkNumber", 0)
                    item.children.map((ele) => {
                        ele.key = ele.unique_code
                        ele.title = ele.name
                        delete ele.children
                        this.$set(ele, 'scopedSlots', { title: 'title_name' })
                    })
                })
            }).finally(() => {
                this.leftLoading = false
            })
        },
        onShow(record) {
            this.visible = true
            let p1 = this.getBusinessTreeData()
            let p2 = this.getTableData()
            Promise.all([p1, p2]).then(res => {
                let all_number = 0
                this.treeData[0].children.map(item => {
                    let item_number = 0
                    item.children.map(ele => {
                        item_number += ele.job_count
                    })
                    this.$set(item, "job_count", item_number)
                    all_number += item_number
                })
                this.treeData[0].job_count = all_number
            })
            if (record) {
                this.active = record
                this.title = "编辑视图"
                this.isEdit = true
                this.spinning = true
                this.getInfomation()
            } else {
                this.title = "新建视图"
                this.isEdit = false
            }
        },
        getInfomation() {
            getOverallView({ code: this.active.code }).then(res => {
                if (res.data) {
                    this.formData = {
                        overall_view_name: res.data.overall_view_name,
                        overall_view_describe: res.data.overall_view_describe,
                        overall_view_type: res.data.overall_view_type,
                        code: res.data.code,
                    }
                    this.selectedRowKeys = res.data.job_code_list
                    this.oldSelectedRowKeys = cloneDeep(this.selectedRowKeys)
                }
            }).finally(() => {
                this.spinning = false
            })
        },
        onClose() {
            this.$refs.ruleForm.resetFields()
            this.formData = this.$options.data().formData
            this.visible = false
            this.selectedRowKeys = this.$options.data().selectedRowKeys
            this.allTableData = this.$options.data().allTableData
            this.tableData = this.$options.data().tableData
            this.treeData = this.$options.data().treeData
            this.treeSelectedKeys = this.$options.data().treeSelectedKeys
            this.tableQuery = this.$options.data().tableQuery

        },
        // 树点击
        treeSelect(selectedKeys, { selected: bool, selectedNodes, node, event }) {
            // console.log(node.dataRef)
            if (node.dataRef.type == "BUSINESS") {
                this.tableData = this.allTableData.filter(item => {
                    return node.dataRef.children.find(ele => {
                        return item.application.name == ele.unique_code
                    })
                })
            } else if (node.dataRef.type == "APPLICATION") {
                this.tableData = this.allTableData.filter(item => {
                    return item.application.name == node.dataRef.unique_code
                })
            } else if (node.dataRef.key == "all") {
                this.tableData = this.allTableData
            }
            this.treeSelectedKeys = [node.dataRef.key]
        },

        onOk() {
            this.$refs.ruleForm.validate(vali => {
                if (vali) {
                    if (this.selectedRowKeys.length == 0) {
                        return this.$message.warning("请选择流水线")
                    }
                    let params = this.formData
                    this.btnLoading = true
                    if (this.isEdit) {
                        let oldArr = this.oldSelectedRowKeys
                        let newArr = this.selectedRowKeys
                        let add_code_list = newArr.filter(item => !oldArr.includes(item))
                        let remove_code_list = oldArr.filter(item => !newArr.includes(item))
                        params.add_code_list = add_code_list
                        params.remove_code_list = remove_code_list
                        editJenkinsViews(params).then(res => {
                            this.$message.success(res.message)
                            this.$emit("ref-list")
                            this.onClose()
                        }).finally(() => {
                            this.btnLoading = false
                        })
                    } else {
                        params.job_code_list = this.selectedRowKeys
                        addJenkinsViews(params).then(res => {
                            this.$message.success(res.message)
                            this.$emit("ref-list")
                            this.onClose()
                        }).finally(() => {
                            this.btnLoading = false
                        })
                    }
                }
            })
        },
    },
}
</script>

<style lang="less" scoped>
footer {
	position: absolute;
	bottom: 0;
	left: 0;
	width: 1000px;
	border-top: 1px solid #e8e8e8;
	padding: 10px 20px;
	background: #fff;
	z-index: 99;
	button {
		float: right;
		margin-right: 20px;
		z-index: 99;
	}
}
.search_box {
	margin: 0 0 10px 0;
}
.box_content {
	border: 1px solid #e8e8e8;
	display: flex;
	padding: 20px;
	.box_content_left {
		flex: 0 0 260px;
		height: 490px;
		overflow-y: auto;
		overflow-x: hidden;
		margin: 0 20px 0 0;
		border-right: 1px solid #e8e8e8;
	}
	.box_content_right {
		flex: 1 1 0px;
	}
}
.ellipsis_row {
	margin: 0;
	width: 100%;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
::-webkit-scrollbar {
	width: 6px;
}
::-webkit-scrollbar-button {
	display: none;
}

::-webkit-scrollbar-track-piece {
	background: #ddd;
	border-radius: 5px;
}
::-webkit-scrollbar-thumb {
	background: #c5c5c5;
	border-radius: 5px;
}
/deep/.ant-tree-node-content-wrapper {
	width: calc(100% - 20px);
	display: inline-block;
}
/deep/.ant-tree-treenode-switcher-close {
	width: 100%;
	.ant-tree-node-content-wrapper {
		width: calc(100% - 20px);
		display: inline-block;
	}
}
/deep/.ant-tree-title {
	width: 100%;
	display: inline-block;
	overflow: hidden;
	text-overflow: ellipsis;
	& > span {
		width: 100%;
		display: inline-block;
		.app_title {
			width: calc(100% - 40px);
			display: inline-block;
			overflow: hidden;
			text-overflow: ellipsis;
		}
		.app_number {
			display: inline-block;
			vertical-align: top;
			padding: 0 10px 0 0;
		}
	}
}
</style>