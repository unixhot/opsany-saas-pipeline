<template>
    <!-- timerTriggerModal 定时触发 -->
    <div>
        <a-table :pagination="false" :columns="columns" :data-source="timerTableData">
            <span slot="action" slot-scope="record">
                <a v-if="record.triggerType !='once'" style="margin:0 10px 0 0px" @click="timerTriggerShow(record)">{{language.edit}}</a>
                <a-tooltip v-else title="该类型不再支持">
                    <span>
                        <a style="margin:0 10px 0 0px" disabled>{{language.edit}}</a>
                    </span>
                </a-tooltip>
                <a @click="deleteCrontab(record)" style="color:red;">{{language.delete}}</a>
            </span>
        </a-table>
        <a-button style="margin:10px 0 0 0;" @click="timerTriggerShow()" icon="plus">{{language.timer_add_timer}}</a-button>
        <a-modal width="800px" @ok="timerHandleOk" v-model="timedTriggerModel" :title="language.timer_title">
            <div class="form_block">
                <p class="form_left">{{language.timer_label1}}：</p>
                <div class="form_right">
                    <a-checkbox v-model="timercheck" style="margin:0 10px 0 0">{{language.timer_label1_message}}</a-checkbox>
                </div>
            </div>

            <div class="form_block">
                <p class="form_left">{{language.timer_label3}}：</p>
                <div class="form_right">
                    <div class="form_line">
                        <a-radio-group v-model="triggerType">
                            <a-radio value="cycle">
                                {{language.timer_radio1}}
                            </a-radio>
                            <!-- <a-radio value="once">
                                {{language.timer_radio2}}
                            </a-radio> -->
                            <a-radio value="date">
                                {{language.timer_radio2}}
                                <a-tooltip title="单次触发为每年执行一次">
                                    <a-icon type="question-circle" />
                                </a-tooltip>
                            </a-radio>
                        </a-radio-group>
                    </div>
                    <div v-if="triggerType=='cycle'" class="form_line">
                        <span class="form_line_left">{{language.timer_label2}}</span>
                        <a-checkbox-group v-model="checkedList" :options="weekOptions" />
                    </div>
                    <div v-if="triggerType=='cycle'" class="form_line">
                        <span class="form_line_left">{{language.timer_time1_1}}</span>
                        <a-time-picker v-model="startTime" :disabledMinutes="getDisabledMinutes" style="margin:0 5px 0 0px;width:120px;" :default-value="moment('12:00', 'HH:mm')" format="HH:mm" />{{language.timer_time1_2}}
                        <a-time-picker v-model="endTime" :disabledMinutes="getDisabledMinutes" style="margin:0 5px 0 0px;width:120px;" :default-value="moment('12:00', 'HH:mm')" format="HH:mm" />
                    </div>
                    <div v-if="triggerType=='cycle'" class="form_line">
                        <span class="form_line_left">{{language.timer_time2}}</span>
                        <a-select v-model="intervalTime" :options="intervalOptions" style="margin:0 5px 0 0px;width:120px;"></a-select>
                    </div>
                    <div v-else-if="triggerType=='once'" class="form_line">
                        <span class="form_line_left">{{language.timer_time3}}</span>
                        <a-time-picker v-model="triggerTime" format="HH:mm" />
                    </div>
                    <div v-else-if="triggerType=='date'" class="form_line">
                        <span class="form_line_left">{{language.timer_time3}}</span>
                        <a-date-picker v-model="triggerTime2" format="MM-DD HH:mm" :show-time="{ defaultValue: moment('00:00:00', 'HH:mm'),format: 'HH:mm' }" />
                    </div>

                </div>
            </div>
        </a-modal>
    </div>
</template>

<script>
import moment from 'moment';
export default {
    data() {
        return {
            // 定时触发弹框
            timedTriggerModel: false,
            checkedList: [],
            // 触发方式
            triggerType: "cycle",
            intervalOptions: [{ value: "5", label: "5分钟" }, { value: "10", label: "10分钟" }, { value: "30", label: "30分钟" }],
            // 定时触发
            timerTableData: [],
            isadd: true,
            // 定时任务触发是否选中
            timercheck: false,
            startTime: moment('8:00', 'HH:mm'),
            endTime: moment('18:00', 'HH:mm'),
            triggerTime: moment('10:00', 'HH:mm'),
            triggerTime2: "",
            intervalTime: 5,
            // 修改的定时对象
            timerObj: {}
        }
    },
    props: ["spec"],
    watch: {
        spec: {
            handler(val, oldval) {
                // console.log(val)
                this.timerTableData = []
                if (!val) {
                    return false
                }
                let specArr = val.split("\n")
                // console.log(specArr)
                specArr.map((spec, index) => {
                    let arr = spec.split(" ")
                    let is_interval // 是否是范围类型的 (1-7)
                    // console.log(arr)
                    let obj
                    if (arr[2] != "*" && arr[3] != "*") {
                        this.triggerType = "date"
                        obj = {
                            key: index,
                            timer: "",
                            crontab: spec,
                            triggerType: "date",
                        }
                        let date = moment().year() + "-" + arr[3] + "-" + arr[2] + " " + arr[1] + ":" + arr[0]
                        // console.log(moment(), moment(date), moment().isBefore(moment(date)))
                        if (moment().isBefore(moment(date))) {
                            obj.timer = date + "\xa0 单次触发"
                            obj.triggerTime = moment(date)
                        } else {
                            date = (moment().year() + 1) + "-" + arr[3] + "-" + arr[2] + " " + arr[1] + ":" + arr[0]
                            obj.timer = date + "\xa0 单次触发"
                            obj.triggerTime = moment(date)
                        }

                    } else {
                        obj = {
                            key: index,
                            checkedList: arr[4].split(","),
                            timer: "",
                            intervalTime: arr[0].split("/")[1]
                        }
                        if (arr[4].indexOf("-") > -1 && arr[4].length == 3) {
                            is_interval = true
                            obj.checkedList = []
                            for (var i = arr[4][0]; i <= arr[4][2]; i++) {
                                obj.checkedList.push(i + "")
                            }
                        }
                        obj.checkedList.map(item => {
                            let week
                            if (item == 0) {
                                week = "星期日"
                            } else if (item == 1) {
                                week = "星期一"
                            } else if (item == 2) {
                                week = "星期二"
                            } else if (item == 3) {
                                week = "星期三"
                            } else if (item == 4) {
                                week = "星期四"
                            } else if (item == 5) {
                                week = "星期五"
                            } else if (item == 6) {
                                week = "星期六"
                            } else if (item == 7) {
                                week = "星期日"
                            }
                            obj.timer += week + ","
                            obj.timer = obj.timer.slice(0, -1) + " / "
                        })
                        if (arr[0].indexOf("H") != -1) {
                            obj.triggerType = "cycle"
                            obj.startTime = moment(arr[1].split("-")[0] + ":00", 'HH:mm')
                            obj.startValue = obj.startTime.format("HH:mm")
                            obj.endTime = moment(arr[1].split("-")[1] + ":00", 'HH:mm')
                            obj.endValue = obj.endTime.format("HH:mm")

                            obj.timer += obj.startValue + " ~ " + obj.endValue + "\xa0 间隔时间 " + obj.intervalTime + " 分钟 周期触发"
                            obj.crontab = "H/" + obj.intervalTime + " " + obj.startValue.split(":")[0] + "-" + obj.endValue.split(":")[0] + " * * "

                            let length = obj.checkedList.length
                            if (length > 1 && obj.checkedList[length - 1] - obj.checkedList[0] == length - 1) {
                                obj.crontab += obj.checkedList[0] + "-" + obj.checkedList[length - 1]
                            } else {
                                obj.crontab += obj.checkedList.join(",")
                            }
                        } else {
                            obj.triggerType = "once"
                            obj.triggerTime = moment(arr[1] + ":" + arr[0], 'HH:mm')
                            obj.triggerValue = obj.triggerTime.format("HH:mm")

                            // table上展示的内容
                            obj.timer += obj.triggerValue + "\xa0 周期触发"
                            // crontab命令
                            obj.crontab = obj.triggerValue.split(":")[1] + " " + obj.triggerValue.split(":")[0] + " * * "
                            let length = obj.checkedList.length
                            if (length > 1 && obj.checkedList[length - 1] - obj.checkedList[0] == length - 1) {
                                obj.crontab += obj.checkedList[0] + "-" + obj.checkedList[length - 1]
                            } else {
                                obj.crontab += obj.checkedList.join(",")
                            }
                        }
                    }
                    // console.log(obj)
                    this.timerTableData.push(obj)
                })
            },
            immediate: true,
        }
    },
    computed: {
        weekOptions() {
            return [
                { value: "0", label: this.language.weekOptions0 },
                { value: "1", label: this.language.weekOptions1 },
                { value: "2", label: this.language.weekOptions2 },
                { value: "3", label: this.language.weekOptions3 },
                { value: "4", label: this.language.weekOptions4 },
                { value: "5", label: this.language.weekOptions5 },
                { value: "6", label: this.language.weekOptions6 },
                // { value: "7", label: this.language.weekOptions0 }
            ]
        },
        columns() {
            return [
                {
                    title: this.language.timer_table1,
                    dataIndex: 'crontab',
                    key: 'crontab',
                    width: 200,
                },
                {
                    title: this.language.timer_table2,
                    dataIndex: 'timer',
                    key: 'timer',
                    width: 500,
                },
                {
                    title: this.language.timer_table3,
                    key: 'action',
                    scopedSlots: { customRender: 'action' },
                    width: 150,
                },
            ]
        }
    },
    created() {
        this.language = this.$store.state.language.languageAuth.pipelineConfiguration || {}
    },
    mounted() {
        // console.log(this.spec)
    },
    methods: {
        moment,
        // 删除
        deleteCrontab(record) {
            let _this = this
            this.$confirm({
                content: "确认删除吗?",
                okType: "danger",
                onOk() {
                    _this.timerTableData.splice(record.key, 1)
                    let spec = ""
                    _this.timerTableData.map((item, index) => {
                        item.key = index
                        spec += item.crontab + "\n"
                    })
                    spec = spec.slice(0, -1)
                    _this.$emit("update:spec", spec)
                }
            })
        },
        // 提交一个定时触发
        timerHandleOk() {
            let obj
            if (this.triggerType == "date") {
                if (!this.triggerTime2) {
                    return this.$message.warning("请选择触发时间")
                }
                // console.log(this.triggerTime2)
                obj = {
                    triggerType: this.triggerType,
                    triggerTime: this.triggerTime2,
                }
                obj.month = obj.triggerTime && obj.triggerTime.format("MM")
                obj.day = obj.triggerTime && obj.triggerTime.format("DD")
                obj.hour = obj.triggerTime && obj.triggerTime.format("HH")
                obj.minute = obj.triggerTime && obj.triggerTime.format("mm")
                obj.crontab = obj.minute + " " + obj.hour + " " + obj.day + " " + obj.month + "  *"
                // console.log(obj)
            } else {
                if (this.checkedList.length == 0) {
                    return this.$message.warning("请选择触发日期")
                }
                if (!this.triggerTime && this.triggerType == "once") {
                    return this.$message.warning("请选择触发时间")
                }
                if (this.triggerType == "cycle") {
                    if (!this.startTime) {
                        return this.$message.warning("请选择触发开始时间")
                    }
                    if (!this.endTime) {
                        return this.$message.warning("请选择触发结束时间")
                    }
                    if (!this.intervalTime) {
                        return this.$message.warning("请选择触发间隔时间")
                    }
                }
                obj = {
                    checkedList: this.checkedList,
                    triggerType: this.triggerType,
                    triggerTime: this.triggerTime,
                    startTime: this.startTime,
                    endTime: this.endTime,
                    intervalTime: this.intervalTime,
                    timer: ""
                }
                obj.triggerValue = obj.triggerTime && obj.triggerTime.format("HH:mm")
                obj.startValue = obj.startTime && obj.startTime.format("HH:mm")
                obj.endValue = obj.endTime && obj.endTime.format("HH:mm")
                if (this.triggerType == "cycle" && obj.startValue > obj.endValue) {
                    return this.$message.warning("请重新选择时间段,开始时间不能大于结束时间")
                }
                obj.checkedList.map(item => {
                    let week
                    if (item == 0) {
                        week = "星期日"
                    } else if (item == 1) {
                        week = "星期一"
                    } else if (item == 2) {
                        week = "星期二"
                    } else if (item == 3) {
                        week = "星期三"
                    } else if (item == 4) {
                        week = "星期四"
                    } else if (item == 5) {
                        week = "星期五"
                    } else if (item == 6) {
                        week = "星期六"
                    } else if (item == 7) {
                        week = "星期日"
                    }
                    obj.timer += week + ","
                })
                obj.timer = obj.timer.slice(0, -1) + " / "
                if (obj.triggerType == "once") {
                    // table上展示的内容
                    obj.timer += obj.triggerValue + "\xa0 周期触发"
                    // crontab命令
                    obj.crontab = obj.triggerValue.split(":")[1] + " " + obj.triggerValue.split(":")[0] + " * * " + obj.checkedList.join(",")
                } else if (obj.triggerType == "cycle") {
                    obj.timer += obj.startValue + " ~ " + obj.endValue + "\xa0 间隔时间 " + obj.intervalTime + " 分钟 周期触发"
                    obj.crontab = "H/" + obj.intervalTime + " " + obj.startValue.split(":")[0] + "-" + obj.endValue.split(":")[0] + " * * " + obj.checkedList.join(",")
                }
            }

            if (this.isadd) {
                this.timerTableData.push(obj)
            } else {
                this.timerTableData[this.timerObj.key] = obj
            }

            this.timedTriggerModel = false
            let spec = ""
            this.timerTableData.map((item, index) => {
                item.key = index
                spec += item.crontab + "\n"
            })
            spec = spec.slice(0, -1)
            this.$emit("update:spec", spec)

        },
        // 定时触发弹框
        timerTriggerShow(record) {
            this.timedTriggerModel = true
            this.checkedList = []
            this.triggerType = this.$options.data().triggerType
            this.triggerTime = moment('10:00', 'HH:mm')
            this.startTime = moment('8:00', 'HH:mm')
            this.endTime = moment('18:00', 'HH:mm')
            this.intervalTime = "5"
            if (record) {
                console.log(record)
                this.timerObj = record
                this.isadd = false
                this.checkedList = record.checkedList
                this.triggerType = record.triggerType
                this.triggerTime = record.triggerTime
                this.triggerTime2 = record.triggerTime
                this.startTime = record.startTime
                this.endTime = record.endTime
                if (this.triggerType == "cycle") {
                    this.intervalTime = record.intervalTime
                }

            } else {
                this.isadd = true
                this.timerObj = {}
            }
        },
        // 不允许选择分钟
        getDisabledMinutes() {
            let arr = []
            for (let i = 1; i <= 60; i++) {
                arr.push(i)
            }
            return arr
        },
    }
}
</script>

<style lang="less" scoped>
.form_block {
	margin: 0 0 20px 0;
	display: flex;
	.form_left {
		flex: 0 0 90px;
	}
	.form_right {
		.form_line {
			margin: 0 0 15px 0;
			.form_line_left {
				display: inline-block;
				width: 70px;
			}
		}
	}
}
</style>