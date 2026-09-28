<template>
    <div class="main">
        <a-card>
            <div slot="title" style="padding:1px 0;">
                <span style="font-size:20px;font-weight:1000;">
                    <a-icon @click="routerBack" type="arrow-left" style="margin-right:10px;font-size:22px;" />
                    <span>执行记录#{{$route.query.number}}</span>
                </span>
            </div>
            <a-spin :spinning="spinning">
                <div class="top_box">
                    <span v-if="activeObj.status == 'SUCCESS'" style="color: #0ba360;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="check-circle" theme="filled" />执行成功
                    </span>
                    <span v-else-if="activeObj.status == 'FAILED'" style="color: red;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="close-circle" theme="filled" />执行失败
                    </span>
                    <span v-else-if="activeObj.status == 'ABORTED'" style="color: #ffa800;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="pause-circle" theme="filled" />停止执行
                    </span>
                    <span v-else-if="activeObj.status == 'WAITING'" style="color: #ffa800;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="hourglass" />等待执行
                    </span>
                    <span v-else-if="activeObj.status == 'UNSTABLE'" style="color: #ffa800;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="exclamation-circle" />不稳定
                    </span>
                    <span v-else-if="activeObj.status == 'IN_PROGRESS'" style="color: #09f;margin: 0">
                        <a-icon style="margin: 0 5px 0 0" type="play-circle" theme="filled" />正在执行
                    </span>
                    <span v-else-if="activeObj.status == 'PAUSED_PENDING_INPUT'" style="color: #09f;">
                        <a-icon style="margin: 0 5px 0 0" type="history" />等待人工确认
                    </span>
                    <span v-else style="margin: 0">
                        {{activeObj.status}}
                    </span>
                    <span>执行人：{{activeObj.username}}</span>
                    <span>执行方式：{{activeObj.req_source}}</span>
                    <span>最近执行时间：{{activeObj.show_last_run_datetime}}</span>
                </div>
                <h4 style="margin:20px 0 10px 0;">
                    <span style="font-weight:1000;">构建过程</span>
                    <span style="color:#888;font-size:12px;margin-left:15px;">可以点击具体构建的步骤查看日志详情</span>
                </h4>
                <div class="pipeline">
                    <div class="stage firststage">
                        <div class="parallelstage">
                            <h4 class="title">
                                <span class="serial">
                                    <a-icon style="font-size:16px;color: #09f" type="caret-right" />
                                </span>
                                <span class="name">开始</span>
                            </h4>
                        </div>
                    </div>
                    <template v-for="(stage,stageindex) in pipelineData">
                        <div v-if="stage.stageFlowNodes && stage.stageFlowNodes.length" class="stage" :key="stageindex">
                            <div class="parallelstage">
                                <h4 class="title">
                                    <span class="serial">
                                        <a-icon v-if="stage.status == 'SUCCESS'" type="check" style="color:#0ba360" />
                                        <a-icon v-else-if="stage.status == 'FAILED'" type="close" style="color:red" />
                                        <a-icon v-else-if="stage.status == 'ABORTED'" type="pause-circle" theme="filled" style="color: #ffa800;" />
                                        <a-icon v-else-if="stage.status == 'WAITING'" type="hourglass" style="color: #ffa800" />
                                        <a-icon v-else-if="stage.status == 'UNSTABLE'" type="exclamation-circle" style="color: #ffa800;" />
                                        <a-icon v-else-if="stage.status == 'IN_PROGRESS'" type="loading" style="color: #09f" />
                                        <a-icon v-else-if="stage.status == 'PAUSED_PENDING_INPUT'" type="history" style="color: #09f;" />
                                    </span>
                                    <span :title="stage.name" class="name">{{stage.name}}</span>
                                    <a-icon class="caret" type="caret-right" />
                                </h4>
                                <template v-if="stage.stageFlowNodes">
                                    <p @click="showSetpDefault(step,'step')" v-for="(step,stepindex) in stage.stageFlowNodes" :key="stepindex" class="step" :class="{select_step:step.id == selectStep.id}">
                                        <span class="span1">
                                            <a-icon v-if="step.status == 'SUCCESS'" type="check" style="color:#0ba360" />
                                            <a-icon v-else-if="step.status == 'FAILED'" type="close" style="color:red" />
                                            <a-icon v-else-if="step.status == 'ABORTED'" type="pause-circle" theme="filled" style="color: #ffa800;" />
                                            <a-icon v-else-if="step.status == 'WAITING'" type="hourglass" style="color: #ffa800" />
                                            <a-icon v-else-if="step.status == 'UNSTABLE'" type="exclamation-circle" style="color: #ffa800;" />
                                            <a-icon v-else-if="step.status == 'IN_PROGRESS'" type="loading" style="color: #09f" />
                                            <a-icon v-else-if="step.status == 'PAUSED_PENDING_INPUT'" type="history" style="color: #09f;" />
                                        </span>
                                        <span class="span2" :title="chName(step)">{{chName(step)}}</span>
                                        <span class="round"></span>
                                    </p>
                                </template>
                            </div>
                        </div>
                        <div v-else-if="stage.children && stage.children.length" class="stage" :key="stageindex">
                            <div v-for="(parallelstage,parallelindex) in stage.children" class="parallelstage" :key="parallelindex">
                                <h4 class="title">
                                    <span class="serial">
                                        <a-icon v-if="parallelstage.status == 'SUCCESS'" type="check" style="color:#0ba360" />
                                        <a-icon v-else-if="parallelstage.status == 'FAILED'" type="close" style="color:red" />
                                        <a-icon v-else-if="parallelstage.status == 'ABORTED'" type="pause-circle" theme="filled" style="color: #ffa800;" />
                                        <a-icon v-else-if="parallelstage.status == 'WAITING'" type="hourglass" style="color: #ffa800" />
                                        <a-icon v-else-if="parallelstage.status == 'UNSTABLE'" type="exclamation-circle" style="color: #ffa800;" />
                                        <a-icon v-else-if="parallelstage.status == 'IN_PROGRESS'" type="loading" style="color: #09f" />
                                        <a-icon v-else-if="parallelstage.status == 'PAUSED_PENDING_INPUT'" type="history" style="color: #09f;" />
                                    </span>
                                    <span :title="parallelstage.name" class="name">{{parallelstage.name}}</span>
                                    <a-icon class="caret" type="caret-right" />
                                </h4>
                                <template v-if="parallelstage.stageFlowNodes && parallelstage.stageFlowNodes.length">
                                    <p @click="showSetpDefault(step,'step')" v-for="(step,stepindex) in parallelstage.stageFlowNodes" :key="stepindex" class="step">
                                        <span class="span1">
                                            <a-icon v-if="step.status == 'SUCCESS'" type="check" style="color:#0ba360" />
                                            <a-icon v-else-if="step.status == 'FAILED'" type="close" style="color:red" />
                                            <a-icon v-else-if="step.status == 'ABORTED'" type="pause-circle" theme="filled" style="color: #ffa800;" />
                                            <a-icon v-else-if="step.status == 'WAITING'" type="hourglass" style="color: #ffa800" />
                                            <a-icon v-else-if="step.status == 'UNSTABLE'" type="exclamation-circle" style="color: #ffa800;" />
                                            <a-icon v-else-if="step.status == 'IN_PROGRESS'" type="loading" style="color: #09f" />
                                            <a-icon v-else-if="step.status == 'PAUSED_PENDING_INPUT'" type="history" style="color: #09f;" />
                                        </span>
                                        <span class="span2" :title="chName(step)">{{chName(step)}}</span>
                                        <span class="round"></span>
                                    </p>
                                </template>
                            </div>
                        </div>
                    </template>

                </div>
            </a-spin>

        </a-card>
        <stepDefalut @updata="updata" ref="stepDefalut"></stepDefalut>

    </div>
</template>

<script>
var moment = require('moment')

import { getJenkinsJobStages, getJenkinsJobStageLogs } from '@/api/assemblyLine'

import stepDefalut from './stepDefalut.vue'
export default {
    data() {
        return {
            pipelineData: [],
            spinning: true,
            activeObj: {},
            destroy: false,
            isStop: false, // 是否停止自动刷新
            selectStep: {},
            isBuilding: false,
        }
    },
    watch: {
        // 是否有流水线正在构建
        isBuilding(newdata, old) {
            // 当isBuilding由true变为false后再获取一次数据
            if (old && !newdata) {
                this.getJenkinsJobStagesData("last")
            }
        },
    },
    beforeRouteEnter(to, from, next) {
        next(vm => {
            vm.$router.replace({ path: to.path, query: { ...vm.$route.query, fromName: from.name || undefined } })
        })
    },
    mounted() {
        this.getJenkinsJobStagesData()
    },
    methods: {
        routerBack() {
            let query = JSON.parse(JSON.stringify(this.$route.query))
            if (query.fromName == "assemblyLine" || query.fromName == "myCollection" || query.fromName == "viewManagement") {
                this.$router.push({ name: this.$route.query.fromName, query: query })
            } else if(query.fromName == "executionLog") {
                this.$router.go(-1)
            } else {
                this.$router.push({ name: "assemblyLine" })
            }
        },
        updata(data) {
            this.getJenkinsJobStagesData().then(() => {
                let flag
                this.pipelineData.map(item => {
                    if (item.children) {
                        item.children.map(ele => {
                            flag = ele.stageFlowNodes.find(step => {
                                return step.id == data.id
                            })
                        })
                    } else {
                        flag = item.stageFlowNodes.find(step => {
                            return step.id == data.id
                        })
                    }
                })
                if (flag) {
                    this.showSetpDefault(flag)
                }
            })
        },
        // 获取执行构建数据
        getJenkinsJobStagesData(last) {
            let params = {
                code: this.$route.query.appCode,
                number: this.$route.query.number,
                job_name: this.$route.query.job_name
            }
            this.$once('hook:beforeDestroy', () => {
                this.destroy = true
            })
            if (this.destroy) {
                return false
            }
            return getJenkinsJobStages(params).then(res => {
                this.activeObj = res.data.opsany_data
                this.activeObj.status = res.data.build_stages?.status
                this.activeObj.show_last_run_datetime = this.activeObj.datetime && moment(this.activeObj.datetime).format("YYYY-MM-DD HH:mm:ss") || "--"
                this.pipelineData = res.data.build_stages?.stages.map(item => {
                    if (item.stageFlowNodes?.length) {
                        if(item.name == "Declarative: Post Actions") {
                            item.name = "结束"
                        }
                        item.stageFlowNodes = item.stageFlowNodes?.filter(ele => {
                            return ele.name != "Get contextual object from internal APIs"
                        })
                    }
                    return item
                })
                this.isBuilding = (res.data.build_stages?.status == "IN_PROGRESS" || res.data.build_stages?.status == "PAUSED_PENDING_INPUT") ? true : false
                res.data.build_stages?.stages.map(item => {
                    if (item.stageFlowNodes?.length > 0) {
                        if (item.parentid) {
                            let parent = this.pipelineData.find(ele => {
                                return ele.id == item.parentid
                            })
                            if (parent) {
                                parent.children.push(item)
                            }
                        }
                    } else {
                        delete item.stageFlowNodes
                        item.children = []
                    }
                })
                this.pipelineData = this.pipelineData.filter(item => {
                    return !item.parentid
                })
                // 状态是正在执行或等待人工确认 轮询刷新数据
                if (res.data.build_stages?.status == "IN_PROGRESS" || res.data.build_stages?.status == "PAUSED_PENDING_INPUT") {
                    if (!this.destroy) {
                        setTimeout(() => {
                            this.getJenkinsJobStagesData()
                        }, 3000)
                    }
                }
                if (!this.isStop) {
                    let stages = res.data.build_stages?.stages
                    let stageFlowNodes = stages[stages.length - 1].stageFlowNodes
                    if (stageFlowNodes?.length) {
                        let step = stageFlowNodes[stageFlowNodes.length - 1]
                        if (res.data.build_stages?.status == "IN_PROGRESS" || res.data.build_stages?.status == "PAUSED_PENDING_INPUT") {
                            this.showSetpDefault(step)
                        } else if (last) {
                            this.showSetpDefault(step)
                        }
                    }
                }
            }).finally(() => {
                this.spinning = false
            })
        },
        showSetpDefault(record, type) {
            this.selectStep = record
            this.$refs.stepDefalut.show(record, type)
        },
        // 将名称转换为中文
        chName(step) {
            if (step.name == "Git") {
                return "拉取代码"
            } else if (step.name == "Print Message") {
                return "打印消息"
            } else if (step.name == "Shell Script") {
                return "执行Shell脚本"
            } else if (step.name == "Sleep") {
                return "睡眠"
            } else if (step.name == "Write file to workspace") {
                return "写文件"
            } else if (step.name == "Read file from workspace") {
                return "读文件"
            } else if (step.name == "codingArtifactsGeneric") {
                return "上传到制品库"
            } else if (step.name == "Wait for interactive input") {
                return "人工确认"
            } else if (step.name == "nexusArtifactUploader") {
                return "上传制品"
            } else if (step.name == "等待交互式输入") {
                return "人工确认"
            } else {
                return step.name
            }
        },
    },
    components: {
        stepDefalut,
    },
}
</script>

<style lang="less" scoped>
.main {
	overflow: auto;
}
.top_box {
	background: #f6f8fa;
	display: flex;
	align-items: center;
	span {
		display: inline-block;
		padding: 10px 30px;
		border-right: 1px solid #ddd;
	}
	span:nth-of-type(1) {
		padding: 25px 30px;
	}
	span:nth-of-type(4) {
		border: none;
	}
}
.pipeline {
	padding: 20px;
	margin: 10px 0 0 0;
	overflow-x: auto;
	overflow-y: auto;
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
			content: "";
			background: #148aff;
			display: inline-block;
			position: absolute;
			top: 20px;
			left: 200px;
			z-index: 4;
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
				content: "";
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
					content: "";
					position: absolute;
					display: inline-block;
					width: 25px;
					height: 1px;
					background: #148aff;
					left: -25px;
					top: 20px;
				}
				&:hover {
					// cursor: pointer;
					// border: 1px solid #148aff;
					.deleteparallel {
						display: inline-block;
						&:hover {
							color: #333;
						}
					}
				}
				.serial {
					background: #98adc347;
					color: #fff;
					display: inline-block;
					height: 38px;
					width: 36px;
					text-align: center;
					line-height: 40px;
					border-radius: 5px 0 0 5px;
				}
				.name {
					padding: 0 0 0 10px;
					display: inline-block;
					width: 158px;
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
				cursor: pointer;
				display: flex;
				&:before {
					position: absolute;
					width: 1px;
					content: "";
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
					width: 160px;
					padding: 0 0 0 10px;
					display: inline-block;
					overflow: hidden;
					text-overflow: ellipsis;
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
			.select_step {
				border: 1px solid #09f;
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
				cursor: pointer;
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
				content: "";
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
	.stage:last-of-type {
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
</style>