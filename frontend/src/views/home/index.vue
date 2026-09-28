<template>
    <div class="home_mian">
        <div class="home_mian_top">
            <div class="cell">
                <div class="cell_left" id="myChart1"></div>
                <div class="cell_right">
                    <h4>{{language.applyOverrides_name}}</h4>
                    <p><span>{{language.applyOverrides_used}}：{{number.use_job}}</span><span>{{language.applyOverrides_notUsed}}：{{number.unused_job}}</span></p>
                </div>
            </div>
            <div class="cell">
                <div class="cell_left" id="myChart2"></div>
                <div class="cell_right">
                    <h4>{{language.pipelineTemplate_name}}</h4>
                    <p>
                        <span>{{language.pipelineTemplate_builtin}}：{{number.built_in_count}}</span>

                        <span>{{language.pipelineTemplate_custom}}：{{number.custom_count}}</span>
                    </p>
                </div>
            </div>
            <div class="cell">
                <div class="cell_left" id="myChart3"></div>
                <div class="cell_right">
                    <h4>{{language.executionStatistics_name}}</h4>
                    <p><span>{{language.executionStatistics_success}}：{{number.job_success_count}}</span><span>{{language.executionStatistics_fail}}：{{number.job_unsuccessful_count}}</span></p>
                </div>
            </div>
            <div class="cell">
                <div class="cell_left" id="myChart4"></div>
                <div class="cell_right">
                    <h4>{{language.executeOnSameday_name}}</h4>
                    <p><span>{{language.executeOnSameday_number}}：{{number.today_task_success_count+number.today_task_error_count}}</span></p>
                </div>
            </div>
        </div>
        <div class="home_main_bottom">
            <div class="bottom_left">
                <h3>{{language.table_title1}}</h3>
                <a-table :loading="leftLoading" @change="tableChange" :dataSource="leftTableData" :columns="leftColumns" :pagination="pagination">
                    <template slot="name" slot-scope="text, record">
                        <a :title="text" @click="$router.push({name:'executionLog',query:{appCode:record.job.application.code,job_name:record.name,fromName:'home'}})">{{text}}</a>
                    </template>
                    <template slot="result" slot-scope="text,record">
                        <span v-if="text == 'SUCCESS'" style="color: #0ba360">
                            <a-icon style="margin: 0 5px 0 0" type="check-circle" theme="filled" />{{language.success}}
                        </span>
                        <span v-else-if="text == 'FAILURE'" style="color: red">
                            <a-icon style="margin: 0 5px 0 0" type="close-circle" theme="filled" />{{language.failed}}
                        </span>
                        <span v-else-if="text == 'ABORTED'" style="color: #ffa800">
                            <a-icon style="margin: 0 5px 0 0" type="pause-circle" /> {{language.stop}}
                        </span>
                        <span v-else-if="text == 'WAITING'" style="color: #ffa800">
                            <a-icon style="margin: 0 5px 0 0" type="hourglass" />等待执行
                        </span>
                        <span v-else-if="text == 'UNSTABLE'" style="color: #ffa800">
                            <a-icon style="margin: 0 5px 0 0" type="exclamation-circle" />不稳定
                        </span>
                        <span v-else-if="record.building" style="color: #09f">
                            <a-icon style="margin: 0 5px 0 0" type="play-circle" theme="filled" />{{language.executing}}
                        </span>
                        <span v-else>
                            {{text}}
                        </span>
                    </template>
                </a-table>
            </div>
            <div class="bottom_right">
                <h3>{{language.table_title2}}</h3>
                <a-table :loading="rightLoading" :dataSource="rightTableData" :columns="rightColumns" :pagination="false">
                    <template slot="index" slot-scope="text">
                        <span :class="{'sort':true,'first':text==1,'second':text==2,'third':text==3}">{{text}}</span>
                    </template>
                </a-table>
            </div>
        </div>
    </div>
</template>

<script>
import { getHomePage, getHomePageSeven, getHomePageUsedApp } from "@/api/home.js"
import { pipelineUpdata } from "@/api/pipelineUpdata.js"
var moment = require('moment')
export default {
    data() {
        return {
            option: {
                title: {
                    text: "",
                    top: "50px",
                    left: "center",
                    subtext: "",
                    subtextStyle: {
                        color: "#333",
                    }
                },

                tooltip: {
                    trigger: 'item'
                },
                legend: {
                    show: false
                },
                series: [
                    {
                        name: '',
                        type: 'pie',
                        color: ['#33A6FF ', '#00D9AB',],
                        radius: ['55%', '70%'],
                        avoidLabelOverlap: false,
                        label: {
                            show: false,
                            position: 'center'
                        },
                        emphasis: {

                        },
                        labelLine: {
                            show: false
                        },
                        data: [
                            { value: 484, name: '已使用' },
                            { value: 300, name: '未使用' }
                        ]
                    }
                ],
            },
            number: {
                use_job: 0,
                unused_job: 0,
                built_in_count: 0,
                custom_count: 0,
                job_success_count: 0,
                job_unsuccessful_count: 0,
                today_task_success_count: 0,
                today_task_error_count: 0,
            },
            leftColumns: [
                { title: "编排名称", dataIndex: "name", scopedSlots: { customRender: 'name' },},
                { title: "所属应用", dataIndex: "application.application_visible_name", ellipsis: true },
                { title: "最后执行状态", dataIndex: "result", width: 115, scopedSlots: { customRender: 'result' }, },
                { title: "最后执行时间", dataIndex: "datetime", width: 170, },
            ],
            rightColumns: [
                { title: "序号", dataIndex: "index", width: 60, scopedSlots: { customRender: 'index' }, },
                { title: "应用名称", dataIndex: "name", width: 200, ellipsis: true },
                { title: "执行任务数", dataIndex: "build_count", width: 100, },
                { title: "最后活跃时间", dataIndex: "datetime", width: 170, },

            ],
            leftTableData: [],
            rightTableData: [],
            pagination: {
                current: 1,
                pageSize: 10,
                total: 0,
                showTotal: (total) => `${this.language.showTotal1} ${total} ${this.language.showTotal2}`,
            },
            leftLoading: false,
            rightLoading: false,
        }
    },
    created() {
        this.language = this.$store.state.language.languageAuth.homeLanguage || {}
        this.leftColumns[0].title = this.language.table_orchestrationName
        this.leftColumns[1].title = this.language.table_application
        this.leftColumns[2].title = this.language.table_status
        this.leftColumns[3].title = this.language.table_time

        this.rightColumns[0].title = this.language.table_number
        this.rightColumns[1].title = this.language.table_name
        this.rightColumns[2].title = this.language.table_tasks
        this.rightColumns[3].title = this.language.table_activeTime
        // console.log(this.language,this.$store.state.language.languageAuth)
    },
    mounted() {
        this.getHomePageData().then(() => {
            this.pipelineUpdata()
        })
        this.getHomePageSevenData(true)
        this.getHomePageUsedAppData(true)
        this.myChart1 = this.$echarts.init(document.getElementById('myChart1'))
        this.myChart2 = this.$echarts.init(document.getElementById('myChart2'))
        this.myChart3 = this.$echarts.init(document.getElementById('myChart3'))
        this.myChart4 = this.$echarts.init(document.getElementById('myChart4'))
        window.addEventListener('resize', this.handleResize);
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.handleResize);
        this.myChart1 && this.myChart1.dispose();
        this.myChart2 && this.myChart2.dispose();
        this.myChart3 && this.myChart3.dispose();
        this.myChart4 && this.myChart4.dispose();
    },
    methods: {
        handleResize() {
            console.log("size")
            this.myChart1.resize();
            this.myChart2.resize();
            this.myChart3.resize();
            this.myChart4.resize();
        },
        // 同步
        pipelineUpdata() {
            pipelineUpdata().then(res => {
                this.getHomePageData()
                this.getHomePageSevenData()
                this.getHomePageUsedAppData()
            })
        },
        tableChange({ current, pageSize }) {
            this.pagination.current = current
            this.pagination.pageSize = pageSize
            this.getHomePageSevenData(true)
        },
        // 获取数据
        getHomePageData() {
            return getHomePage().then(res => {
                if (res.data) {
                    let number = {
                        use_job: res.data.job_cover.use_job,
                        unused_job: res.data.job_cover.unused_job,
                        built_in_count: res.data.job_template.built_in_count,
                        custom_count: res.data.job_template.custom_count,
                        job_success_count: res.data.job_status.job_success_count,
                        job_unsuccessful_count: res.data.job_status.job_unsuccessful_count,
                        today_task_success_count: res.data.today_job.today_task_success_count,
                        today_task_error_count: res.data.today_job.today_task_error_count,
                    }
                    this.number = number
                    let option1 = JSON.parse(JSON.stringify(this.option))
                    let option2 = JSON.parse(JSON.stringify(this.option))
                    let option3 = JSON.parse(JSON.stringify(this.option))
                    let option4 = JSON.parse(JSON.stringify(this.option))
                    option1.series[0].data = [
                        { value: number.use_job, name: '已使用' },
                        { value: number.unused_job, name: '未使用' },
                    ]
                    option2.series[0].data = [
                        { value: number.built_in_count, name: '内置模板' },
                        { value: number.custom_count, name: '自定义模板' },
                    ]
                    option3.series[0].data = [
                        { value: number.job_success_count, name: '成功' },
                        { value: number.job_unsuccessful_count, name: '失败' },
                    ]
                    option4.series[0].data = [
                        { value: number.today_task_success_count, name: '成功次数' },
                        { value: number.today_task_error_count, name: '失败次数' },
                    ]
                    if (number.use_job + number.unused_job) {
                        option1.title.text = parseInt(number.use_job / (number.use_job + number.unused_job) * 100) + "%"
                    } else {
                        option1.title.text = 0
                    }
                    option1.title.subtext = this.language.applyOverrides_Coverage
                    option2.title.text = number.built_in_count + number.custom_count
                    option2.title.subtext = this.language.pipelineTemplate_total
                    if (number.job_success_count + number.job_unsuccessful_count > 0) {
                        option3.title.text = parseInt(number.job_success_count / (number.job_success_count + number.job_unsuccessful_count) * 100) + "%"
                    } else {
                        option3.title.text = 0
                    }
                    option3.title.subtext = this.language.executionStatistics_successRate
                    option4.title.text = number.today_task_success_count + number.today_task_error_count
                    option4.title.subtext = this.language.executeOnSameday_total

                    let myChart1 = this.$echarts.init(document.getElementById('myChart1'))
                    let myChart2 = this.$echarts.init(document.getElementById('myChart2'))
                    let myChart3 = this.$echarts.init(document.getElementById('myChart3'))
                    let myChart4 = this.$echarts.init(document.getElementById('myChart4'))
                    myChart1.setOption(option1);
                    myChart2.setOption(option2);
                    myChart3.setOption(option3);
                    myChart4.setOption(option4);
                }
            }).catch(() => {
                let option1 = JSON.parse(JSON.stringify(this.option))
                let option2 = JSON.parse(JSON.stringify(this.option))
                let option3 = JSON.parse(JSON.stringify(this.option))
                let option4 = JSON.parse(JSON.stringify(this.option))
                option1.series[0].data = [
                    { value: 0, name: '已使用' },
                    { value: 0, name: '未使用' },
                ]
                option2.series[0].data = [
                    { value: 0, name: '内置模板' },
                    { value: 0, name: '自定义模板' },
                ]
                option3.series[0].data = [
                    { value: 0, name: '成功' },
                    { value: 0, name: '失败' },
                ]
                option4.series[0].data = [
                    { value: 0, name: '成功次数' },
                    { value: 0, name: '失败次数' },
                ]

                option1.title.text = 0
                option1.title.subtext = this.language.applyOverrides_Coverage
                option2.title.text = 0
                option2.title.subtext = this.language.pipelineTemplate_total
                option3.title.text = 0
                option3.title.subtext = this.language.executionStatistics_successRate
                option4.title.text = 0
                option4.title.subtext = this.language.executeOnSameday_total

                let myChart1 = this.$echarts.init(document.getElementById('myChart1'))
                let myChart2 = this.$echarts.init(document.getElementById('myChart2'))
                let myChart3 = this.$echarts.init(document.getElementById('myChart3'))
                let myChart4 = this.$echarts.init(document.getElementById('myChart4'))
                myChart1.setOption(option1);
                myChart2.setOption(option2);
                myChart3.setOption(option3);
                myChart4.setOption(option4);
            })
        },
        // 获取最近七天数据
        getHomePageSevenData(loading) {
            if (loading) {
                this.leftLoading = true
            }
            let updata = {
                current: this.pagination.current,
                pageSize: this.pagination.pageSize,
            }
            getHomePageSeven(updata).then(res => {
                this.pagination.total = res.data.total
                if (res.data && res.data.data) {
                    this.leftTableData = res.data.data
                    res.data.data.map(item => {
                        item.key = item.code
                        item.name = item.job.job_name
                        item.application = item.job.application
                    })
                }
            }).finally(() => {
                this.leftLoading = false
            })
        },
        // 获取应用使用频率排名
        getHomePageUsedAppData(first) {
            if (first) {
                this.rightLoading = true
            }
            getHomePageUsedApp({ length: 8 }).then(res => {
                if (res.data) {
                    this.rightTableData = res.data.filter(item => {
                        return item.build_count > 0
                    })
                    res.data.map((item, index) => {
                        item.key = item.code
                        item.index = index + 1
                        item.datetime = item.datetime || "--"
                    })
                }
            }).finally(() => {
                this.rightLoading = false
            })
        }
    },
}
</script>

<style lang="less" scoped>
.home_mian {
    .home_mian_top {
        display: flex;
        margin: 6px 0 0 0;
        flex: 1 1 0;
        .cell {
            display: flex;
            align-items: center;
            background: #fff;
            flex: 1 1 0;
            margin: 0 10px 0 10px;
            h4 {
                font-size: 20px;
            }
            span {
                white-space: pre;
            }
            span:nth-of-type(1) {
                margin: 0 10px 0 0;
            }
        }
    }
    .home_main_bottom {
        margin: 16px 0 0 0;
        display: flex;
        .bottom_left {
            flex: 1 1 0;
            margin: 0 10px;
            background: #fff;
        }
        .bottom_right {
            flex: 1 1 0;
            margin: 0 10px;
            background: #fff;
            .sort {
                width: 30px;
                height: 32px;
                text-align: center;
                line-height: 22px;
                color: #fff;
                display: inline-block;
                background-image: url('~@/assets/image/fourth.png');
                background-size: 30px;
                background-repeat: no-repeat;
            }
            .first {
                background-image: url('~@/assets/image/first.png');
            }
            .second {
                background-image: url('~@/assets/image/second.png');
            }
            .third {
                background-image: url('~@/assets/image/second.png');
            }
        }
        h3 {
            padding: 12px 0 12px 16px;
            margin: 0;
            font-size: 16px;
            border-bottom: 1px solid #e8e8e8;
        }
        .ant-table-wrapper {
            padding: 16px;
        }
    }
}
.cell_left {
    width: 150px;
    height: 150px;
}
@media (max-width: 1600px) {
    .home_mian .home_mian_top .cell h4 {
        font-size: 16px;
    }
    .home_mian .home_mian_top .cell span {
        display: block;
    }
}

@media (max-width: 1400px) {
    .home_mian .home_main_bottom {
        display: block;
        .bottom_right {
            margin: 16px 10px 0;
        }
    }
    .home_mian .home_mian_top .cell span {
        font-size: 12px;
    }
    .cell_left {
        width: 120px;
    }
}
</style>