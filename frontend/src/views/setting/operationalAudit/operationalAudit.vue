<template>
    <div>
        <content-header>
            <div slot="docs">对流水线所有的变更，都会进行变更记录。</div>
        </content-header>
        <a-card>
            <div class="search_top">
                <a-input-search v-model="tableQuery.search_data" @search="searchTable" :placeholder="language.placeholder" style="width: 300px" allowClear>
                    <a-select slot="addonBefore" style="width: 100px" v-model="tableQuery.search_type">
                        <a-select-option :title="item.name" v-for="item in searchList" :key="item.key">{{ item.name }}</a-select-option>
                    </a-select>
                </a-input-search>
                <span style="margin:0 10px 0 20px;">{{language.searchList3}} :</span>
                <a-select @change="searchTable" v-model="tableQuery.operation_type" style="width:200px;">
                    <a-select-option v-for="item in operationTypeList" :key="item.key">{{item.label}}</a-select-option>
                </a-select>
            </div>
            <a-table :row-key="(record) => record.code" @change="tableChange" :loading="tableLoading" :columns="columns" :dataSource="tableData" :pagination="{
                ...tableQuery,showSizeChanger: true,showTotal: (total) => `共 ${total} 条数据`,showQuickJumper: true,
                pageSizeOptions: ['10','20','40','50','100','150','200',],}" :scroll="{x:1000}">
                <template slot="version" slot-scope="text, record">
                    <a @click="$refs.OperationDetails.showModal(record)">{{ text }}</a>
                </template>
                <template slot="user_username" slot-scope="text, record">
                    <span v-if="record.user_username" :title="`${record.user_ch_name || record.user_username}(${record.user_username})`">{{ record.user_ch_name || record.user_username }}({{ record.user_username }})</span>
                    <span v-else>--</span>
                </template>
                <template slot="operation_type" slot-scope="text, record">
                    <span>{{record.show_operation_type}}</span>
                </template>

            </a-table>
            <OperationDetails ref="OperationDetails"></OperationDetails>
        </a-card>
    </div>
</template>

<script>
import OperationDetails from "./operationDetails.vue"
import { getOperationAudit } from "@/api/operationalAudit.js"
export default {
    data() {
        return {
            tableData: [],
            tableQuery: {
                search_type: 'user_username',
                search_data: undefined,
                current: 1,
                pageSize: 10,
                total: 0,
                operation_type: "",
                // start_min_time: undefined,
                // start_max_time: undefined,
            },
            tableLoading: false,
            // operation_type  1新建  2删除  3编辑
        }
    },
    computed: {
        searchList() {
            return [
                { name: this.language.searchList1, key: 'user_username' },
                { name: this.language.searchList2, key: 'operation_object_name' },
            ]
        },
        // 操作类型
        operationTypeList() {
            return [
                { key: "", label: this.language.operationType0 },
                { key: 1, label: this.language.operationType1 },
                { key: 2, label: this.language.operationType2 },
                { key: 3, label: this.language.operationType3 },
            ]
        },
        columns() {
            return [
                {
                    title: this.language.columns1,
                    dataIndex: 'version',
                    scopedSlots: { customRender: 'version' },
                    ellipsis: true,
                    width: 180,
                },
                {
                    title: this.language.columns2,
                    dataIndex: 'user_username',
                    scopedSlots: { customRender: 'user_username' },
                    ellipsis: true,
                    width: 170,
                },
                {
                    title: this.language.columns3,
                    dataIndex: 'operation_object_name',
                    ellipsis: true,
                    width: 270
                },
                {
                    title: this.language.columns4,
                    dataIndex: 'operation_type',
                    scopedSlots: { customRender: 'operation_type' },
                    width: 100,
                },
                {
                    title: this.language.columns5,
                    dataIndex: 'describe',
                    ellipsis: true,
                    width: 170,
                },
                {
                    title: this.language.columns6,
                    dataIndex: 'create_time',
                    width: 170,
                },
            ]
        },
    },
    mounted() {
        this.getTableData()
    },
    created() {
        this.language = Object.assign({}, this.$store.state.language.languageAuth.public1 || {}, this.$store.state.language.languageAuth.operationalAudit || {})
    },
    methods: {
        // 搜索
        searchTable() {
            this.tableQuery.current = 1
            this.getTableData()
        },
        // 获取table数据
        getTableData() {
            let params = { ...this.tableQuery }
            this.tableLoading = true
            getOperationAudit(params).then(res => {
                if (res.data.total > 0 && res.data.data.length == 0 && res.data.page > 1) {
                    this.tableQuery.current--
                    return this.tableData()
                }
                this.tableQuery.total = res.data.total
                res.data.data.forEach(item => {
                    item.show_operation_type = this.operationTypeList.find(ele => {
                        return ele.key == item.operation_type
                    })?.label
                })
                this.tableData = res.data.data
            }).finally(() => {
                this.tableLoading = false
            })
        },
        tableChange({ current, pageSize }) {
            this.tableQuery.current = current
            this.tableQuery.pageSize = pageSize
            this.getTableData()
        },
    },
    components: {
        OperationDetails,
    }
}
</script>
<style lang="less" scoped>
.search_top {
	margin: 0 0 10px 0;
}
</style>