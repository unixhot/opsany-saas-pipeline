<template>
    <div>
        <a-card>
            <div slot="title" style="display:flex;align-items:center;justify-content:space-between">
                <div style="display:flex;align-items:center;font-weight:1000;">
                    <a-icon @click="routerBack" style="font-size:22px;margin-right:10px;cursor:pointer" type="arrow-left" />
                    <span style="font-size:20px;">{{title}}</span>
                </div>
                <a-button :loading="tableLoading" @click="getTableData(true)" icon="reload" style="float: right">刷新</a-button>
            </div>
            <a-table :row-key="(record) => record.code" :loading="{spinning:tableLoading,tip:'正在加载中，请耐心等待...'}" :expandIconColumnIndex="6" :key="tableKey" @expand="onexpand" :expandIconAsCell="false" :defaultExpandAllRows="true" :columns="columns" :dataSource="tableData" :pagination="false">
                <span slot="result" slot-scope="text, record">
                    <p v-if="text == 'SUCCESS'" style="color: #0ba360;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="check-circle" theme="filled" />{{ language.succeeded }}
                    </p>
                    <p v-else-if="text == 'FAILURE'" style="color: red;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="close-circle" theme="filled" />{{language.failed}}
                    </p>
                    <p v-else-if="text == 'ABORTED'" style="color: #ffa800;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="pause-circle" theme="filled" />{{ language.stop_result }}
                    </p>
                    <p v-else-if="text == 'WAITING'" style="color: #ffa800;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="hourglass" />等待执行
                    </p>
                    <p v-else-if="text == 'UNSTABLE'" style="color: #ffa800;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="exclamation-circle" />不稳定
                    </p>
                    <p v-else-if="text == 'PENDING'" style="margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="clock-circle" />等待确认
                    </p>
                    <p v-else-if="record.building" style="color: #09f;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="play-circle" theme="filled" />{{language.executing}}
                    </p>
                    <p v-else style="margin: 0">
                        {{text}}
                    </p>
                </span>
                <span slot="number" slot-scope="text, record">
                    <span v-if="text">
                        <a v-if="$store.state.btnAuth.btnAuth" @click="routerGoto(record)">#{{ text }}</a>
                        <span v-else>#{{ text }}</span>
                    </span>
                    <span v-else>--</span>
                </span>
                <span slot="action" slot-scope="record">
                    <span>
                        <a v-if="record.number" style="margin: 0 10px 0 0px" @click="routerGoto(record)">查看详情</a>
                        <a v-if="record.number" @click="$refs.ImplementationDetails.show(job_name,record.number,$route.query.view_name)" style="margin: 0 10px 0 0px">查看日志</a>
                        <a v-if="can_delete_log" style="margin: 0 10px 0 0px" @click="deleteHistory(record)">{{ language.delete }}</a>
                        <a v-if="record.building && can_stop" @click="stopExecution(record)" style="color: orange;">{{ language.stop }}</a>
                    </span>
                </span>
            </a-table>
        </a-card>
        <ImplementationDetails ref="ImplementationDetails"></ImplementationDetails>
    </div>
</template>

<script>
var moment = require('moment')
import { getBuildHistory, deleteHistory, stopExecution } from '@/api/assemblyLine'

import ImplementationDetails from './components/implementationDetails.vue'
export default {
    data() {
        return {
            visible: false,
            title: "执行历史",
            tableLoading: false,
            tableData: [],
            columns: [
                { title: '执行编号', dataIndex: 'number', key: 'number', scopedSlots: { customRender: 'number' }, width: 100, },
                { title: '状态', dataIndex: 'result', key: 'result', scopedSlots: { customRender: 'result' }, width: 120, },
                { title: '持续时间', dataIndex: 'duration_str', key: 'duration_str', width: 100, customRender: text => (text != '0' && text) || '--' },
                { title: '执行方式', dataIndex: 'req_source', key: 'req_source', customRender: (text) => { return text || '--' }, width: 100, ellipsis: true, },
                { title: '执行人', dataIndex: 'username', customRender: (text) => text || '--', width: 100, },
                { title: '执行时间', dataIndex: 'timestamp_show', key: 'timestamp_show', width: 170, },
                { title: '操作', scopedSlots: { customRender: 'action' }, width: 170, align: 'center', },
            ],
            appCode: 0,
            // 是否停止调取流水线数据
            isStop: false,
            // 是否停止循环请求接口
            destroy: false,
            can_stop: false,
            can_delete_log: false,
            expandedRowKeys: [],
            tableKey: 1,
        }
    },
    beforeRouteEnter(to, from, next) {
        next(vm => {
            vm.$router.replace({ path: to.path, query: { ...vm.$route.query, } })
        })
    },
    mounted() {
        this.title = this.$route.query.job_name + "-执行历史"
        this.job_name = this.$route.query.job_name
        this.appCode = this.$route.query.appCode
        this.job_code = this.$route.query.job_code // 流水线的唯一标识code
        this.view_name = this.$route.query.view_name // 流水线的名称
        this.getTableData(true)
        setTimeout(() => {
            this.loop()
        }, 5000)
        this.$once('hook:beforeDestroy', () => {
            this.destroy = true
        })
    },
    created() {
        this.language = this.$store.state.language.languageAuth.assemblyLineLanguage || {}
    },
    methods: {
        routerGoto(record) {
            console.log(record)
            this.$router.push({ name: 'executionLogDefault', query: { appCode: this.appCode, number: record.number, 
                job_name: this.job_name, job_code: this.job_code, build_code: record.code } })
        },
        onexpand(expanded, record) {
        },
        routerBack() {
            let query = JSON.parse(JSON.stringify(this.$route.query))
            if (query.fromName == "assemblyLine" || query.fromName == "myCollection" || query.fromName == "viewManagement") {
                this.$router.push({ name: this.$route.query.fromName, query: query })
            } else {
                this.$router.go(-1)
            }
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
        getTableData(loading) {
            let flag = false
            this.$once('hook:beforeDestroy', () => {
                this.destroy = true
                flag = true
            })
            if (loading) {
                this.tableLoading = true
            }
            return getBuildHistory({ code: this.appCode, job_name: this.job_name }).then(res => {
                this.tableKey++
                this.can_delete_log = res.data.can_delete_log
                this.can_stop = res.data.can_stop
                this.tableData = res.data?.build_list
                this.expandedRowKeys = res.data?.build_list.map((item) => {
                    if (!item.timestamp || item.timestamp == 0) {
                        item.timestamp_show = '--'
                    } else {
                        item.timestamp_show = item.datetime && moment(item.datetime).format("YYYY-MM-DD HH:mm:ss")
                    }
                    return item.code
                })
            }).catch(() => {
                this.isStop = true
            }).finally(() => {
                this.tableLoading = false
            })
        },
        // 删除历史记录
        deleteHistory(record) {
            let _this = this
            this.$confirm({
                content: '确认删除该条记录吗？',
                okType: "danger",
                onOk() {
                    return new Promise((resolve, reject) => {
                        deleteHistory({
                            app_code: _this.appCode,
                            name: _this.job_name,
                            number: record.number,
                            build_code: record.code,
                        }).then((res) => {
                            if (res.code == 200) {
                                _this.getTableData(true)
                                _this.$message.success(res.message)
                                resolve()
                            } else {
                                _this.$message.error(res.message)
                            }
                        }).finally(() => {
                            reject()
                        })
                    })
                },
            })
        },
        // 停止执行
        stopExecution(record) {
            let _this = this
            this.$confirm({
                content: '确认停止执行吗？',
                onOk() {
                    return stopExecution({
                        code: _this.appCode,
                        name: _this.job_name,
                        number: record.number,
                        view_name: _this.$route.query.view_name,
                    }).then((res) => {
                        if (res.code == 200) {
                            _this.getTableData(true)
                            _this.$message.success(res.message)
                        } else {
                            _this.$message.error(res.message)
                        }
                    })
                },
            })
        },
    },
    components: {
        ImplementationDetails,
    }
}
</script>

<style>
</style>