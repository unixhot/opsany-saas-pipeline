<template>
    <div>
        <content-header>
            <div slot="docs">如果需要拉取Git仓库等操作，需要提前创建好凭据。</div>
        </content-header>
        <a-card>
            <div class="search_top">
                <a-input-search v-model="tableQuery.search_data" @search="searchTable" :placeholder="language.placeholder" style="width: 300px" allowClear>
                    <a-select slot="addonBefore" style="width: 100px" v-model="tableQuery.search_type">
                        <a-select-option :title="item.name" v-for="item in searchList" :key="item.key">{{ item.name }}</a-select-option>
                    </a-select>
                </a-input-search>
                <a-button v-if="$store.state.btnAuth.btnAuth.pipeline_credentials_create" :loading="btnLoading" @click="$refs.AddCredentialModel.show()" type="primary" icon="plus" style="float: right;margin:0 0 0 10px;">{{language.addCredentials}}</a-button>
                <a-button @click="getTableData()" icon="reload" style="float: right">{{language.reload}}</a-button>
            </div>

            <a-table :row-key="(record) => record.code" @change="tableChange" :loading="{spinning:tableLoading,tip:'正在加载中，请耐心等待...'}" :columns="columns" :dataSource="tableData" :pagination="{
                ...tableQuery,showSizeChanger: true,showTotal: (total) => `共 ${total} 条数据`,showQuickJumper: true,
                pageSizeOptions: ['10','20','40','50','100','150','200',],}" :scroll="{x:1000}">
                <span slot="scope" slot-scope="text, record">
                    <span v-if="record.is_inner" :title="record.application && record.application.visible_name">{{record.application && record.application.visible_name}}</span>
                    <span v-else>{{text}}</span>
                </span>
                <span slot="action" slot-scope="text, record">
                    <span>
                        <a v-if="$store.state.btnAuth.btnAuth.pipeline_credentials_update" @click="$refs.AddCredentialModel.show(record)">{{language.edit}}</a>
                        <a v-if="$store.state.btnAuth.btnAuth.pipeline_credentials_delete" @click="deleteCredentials(record)" style="margin: 0 0 0 10px; color: red">{{language.delete}}</a>
                        <span v-if="!$store.state.btnAuth.btnAuth.pipeline_credentials_update && !$store.state.btnAuth.btnAuth.pipeline_credentials_delete">--</span>
                    </span>
                </span>
            </a-table>
        </a-card>
        <AddCredentialModel @father="getTableData" :credentialsTypeList.sync="credentialsTypeList" ref="AddCredentialModel"></AddCredentialModel>

    </div>
</template>

<script>
import AddCredentialModel from './model/addCredential.vue'

import { getTableCredentials, getCredentialsType, deleteCredentials } from "@/api/credential.js"
export default {
    data() {
        return {
            tableData: [],
            tableQuery: {
                search_type: 'name',
                search_data: undefined,
                current: 1,
                pageSize: 10,
                total: 0,
            },
            tableLoading: false,
            credentialsTypeList: [],
            btnLoading: false,
        }
    },
    created() {
        this.language = Object.assign({}, this.$store.state.language.languageAuth.public1 || {}, this.$store.state.language.languageAuth.credentialManagement || {})
    },
    computed: {
        searchList() {
            return [
                { name: this.language.searchList1, key: 'name' },
                { name: this.language.searchList2, key: 'credentials_id' },
            ]
        },
        columns() {
            return [
                { title: this.language.columns1, dataIndex: 'name', key: 'name', },
                { title: this.language.columns2, dataIndex: 'credentials_id', key: 'credentials_id', },
                { title: this.language.columns3, dataIndex: 'type_name', key: 'type_name', width: 100, },
                { title: this.language.columns4, key: 'scope', dataIndex: 'scope', scopedSlots: { customRender: 'scope' }, width: 150, ellipsis: true, },
                { title: this.language.columns5, key: 'created_at', dataIndex: 'created_at', width: 170, },
                { title: this.language.columns6, key: 'action', scopedSlots: { customRender: 'action' }, fixed: "right", width: 120, align: "center", },
            ]
        }
    },
    mounted() {
        this.getCredentialsTypeData()
        this.getTableData()
    },
    methods: {
        getTableData() {
            let params = { ...this.tableQuery }
            this.tableLoading = true
            getTableCredentials(params).then(res => {
                if (res.data.total > 0 && res.data.data.length == 0 && res.data.page > 1) {
                    this.tableQuery.current--
                    return this.tableData()
                }
                this.tableQuery.total = res.data.total
                res.data.data.map((item) => {
                    item.key = item.code
                    if (item.is_inner) {
                        item.scope = this.language.scope1
                    } else {
                        item.scope = this.language.scope2
                    }
                    if (item.typeName == 'SSH Username with private key') {
                        item.type = 4
                        item.type_name = this.language.type_name1
                    } else if (item.typeName == 'Username with password') {
                        item.type = 0
                        item.type_name = this.language.type_name2
                    } else if (item.typeName == 'GitLab API token') {
                        item.type = 2
                        item.type_name = this.language.type_name3
                    } else if(item.typeName == 'Secret text') {
                        item.type = 6
                        item.type_name = this.language.type_name4
                    }
                })
                this.tableData = res.data.data
            }).finally(() => {
                this.tableLoading = false
            })
        },
        // 搜索
        searchTable() {
            this.tableQuery.current = 1
            this.getTableData()
        },
        tableChange({ current, pageSize }) {
            this.tableQuery.current = current
            this.tableQuery.pageSize = pageSize
            this.getTableData()
        },
        // 获取类型数据
        getCredentialsTypeData() {
            this.btnLoading = true
            getCredentialsType().then((res) => {
                if (res.code == 200 && res.data) {
                    this.credentialsTypeList = res.data
                }
            }).finally(()=>{
                this.btnLoading = false
            })
        },
        // 删除
        deleteCredentials(record) {
            let _this = this
            this.$confirm({
                content: this.language.deleteMessage1,
                okType: "danger",
                onOk() {
                    return new Promise((resolve, reject) => {
                        deleteCredentials({ code: record.code, }).then(
                            (res) => {
                                if (res.code == 200) {
                                    _this.$message.success(res.message)
                                    _this.getTableData()
                                    resolve()
                                } else {
                                    _this.$message.error(res.message)
                                }
                            }
                        ).finally(() => {
                            reject()
                        })
                    })
                },
            })
        },
    },
    components: {
        AddCredentialModel,
    }
}
</script>

<style lang="less" scoped>
.search_top {
	margin: 0 0 10px 0;
}
</style>