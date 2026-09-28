<template>
    <a-drawer :bodyStyle="{ padding: '24px 24px 64px 24px' }" width="1300px" :title="title" placement="right" :visible="visible" @close="onClose">
        <a-spin :spinning="spinning">
            <a-collapse default-active-key="1" :bordered="false">
                <a-collapse-panel key="1" :header="language.collapse1">
                    <a-row :gutter="[16,16]">
                        <a-col :span="12">
                            <span class="box_title">{{language.label1}} :</span>
                            <span class="box_content">
                                <span v-if="infomation.user_username">{{ infomation.user_ch_name || infomation.user_username }}({{ infomation.user_username }})</span>
                                <span v-else>--</span>
                            </span>
                        </a-col>
                        <a-col :span="12">
                            <span class="box_title">{{language.label2}} :</span>
                            <span class="box_content">{{infomation.operation_object_name}}</span>
                        </a-col>
                        <a-col :span="12">
                            <span class="box_title">{{language.label3}} :</span>
                            <span class="box_content">{{infomation.show_operation_type}}</span>
                        </a-col>
                        <a-col :span="12">
                            <span class="box_title">{{language.label4}} :</span>
                            <span class="box_content">{{infomation.describe}}</span>
                        </a-col>
                        <a-col :span="12">
                            <span class="box_title">{{language.label5}} :</span>
                            <span class="box_content">{{infomation.create_time}}</span>
                        </a-col>
                    </a-row>

                </a-collapse-panel>
            </a-collapse>
            <a-collapse default-active-key="1" :bordered="false">
                <a-collapse-panel key="1" :header="language.collapse2">
                    <div class="title">
                        <div>
                            <p>{{language.before}}</p>
                            <span>{{infomation.show_operation_detail}}</span>
                        </div>
                        <div>
                            <p>{{language.after}}</p>
                            <span>{{infomation.show_operation_detail}}</span>
                        </div>
                    </div>
                    <div class="content" v-if="infomation.operation_detail==1">
                        <div class="content_left grey">
                            {{language.detailMessage1}}
                        </div>
                        <div class="content_right green">
                            {{language.detailMessage2}}【{{infomation.operation_object_name}}】
                        </div>
                    </div>
                    <div class="content" v-if="infomation.operation_detail==2">
                        <div class="content_left grey">
                            {{language.detailMessage3}}【{{infomation.operation_object_name}}】
                        </div>
                        <div class="content_right green">
                            {{language.detailMessage4}}【{{infomation.operation_object_name}}】
                        </div>
                    </div>
                    <code-diff v-if="infomation.operation_detail>2" :context="9999" :isShowNoChange="true" :old-string="contentLeft" :new-string="contentRight" outputFormat="side-by-side" />
                </a-collapse-panel>
            </a-collapse>
        </a-spin>

    </a-drawer>
</template>

<script>
import CodeDiff from 'vue-code-diff'
import { getOperationLog } from "@/api/operationalAudit.js"
export default {
    data() {
        return {
            visible: false,
            infomation: {},
            spinning: false,
            contentLeft: "",
            contentRight: "",

            // operation_detail     1：新建流水线  2：删除流水线    3：编辑基础信息    4：编辑流程配置  5：编辑触发规则  6：编辑参数设置
        }
    },
    created() {
        this.language = Object.assign({}, this.$store.state.language.languageAuth.public1 || {}, this.$store.state.language.languageAuth.operationalAudit || {})
    },
    computed: {
        title() {
            return this.language.detailTitle
        },
        // 操作类型
        operationTypeList() {
            return [
                { key: 1, label: this.language.operationType1 },
                { key: 2, label: this.language.operationType2 },
                { key: 3, label: this.language.operationType3 },
            ]
        },
        // 操作类型(详细)
        operationDetailList() {
            return [
                { key: 1, label: this.language.operationDetail1 },
                { key: 2, label: this.language.operationDetail2 },
                { key: 3, label: this.language.operationDetail3 },
                { key: 4, label: this.language.operationDetail4 },
                { key: 5, label: this.language.operationDetail5 },
                { key: 6, label: this.language.operationDetail6 },
            ]
        },
    },
    methods: {
        onClose() {
            this.visible = false
            this.contentLeft = this.$options.data().contentLeft
            this.contentRight = this.$options.data().contentRight
            this.infomation = this.$options.data().infomation
        },
        showModal(record) {
            this.visible = true
            this.spinning = true
            this.getInfomationData(record)
        },
        getInfomationData(record) {
            this.spinning = true
            getOperationLog({ log_code: record.code }).then(res => {
                res.data.show_operation_type = this.operationTypeList.find(ele => {
                    return ele.key == res.data.operation_type
                })?.label
                res.data.show_operation_detail = this.operationDetailList.find(ele => {
                    return ele.key == res.data.operation_detail
                })?.label
                if (res.data.operation_detail == 3) {
                    this.contentLeft = JSON.stringify(res.data.before_change_dict, null, 4)
                    this.contentRight = JSON.stringify(res.data.after_change_dict, null, 4)
                } else if (res.data.operation_detail == 4) {
                    this.contentLeft = res.data.before_change_dict.before_update_config
                    this.contentRight = res.data.after_change_dict.after_update_config
                } else if (res.data.operation_detail == 5) {
                    this.contentLeft = JSON.stringify(res.data.before_change_dict, null, 4)
                    this.contentRight = JSON.stringify(res.data.after_change_dict, null, 4)
                } else if (res.data.operation_detail == 6) {
                    this.contentLeft = JSON.stringify(res.data.before_change_dict, null, 4)
                    this.contentRight = JSON.stringify(res.data.after_change_dict, null, 4)
                }

                this.infomation = res.data
            }).finally(() => {
                this.spinning = false
            })
        }
    },
    components: {
        CodeDiff,
    }
}
</script>
<style lang="less" scoped>
.box_title {
	margin: 0 15px 0 0;
	color: #666;
	width: 100px;
	display: inline-block;
	text-align: right;
}
.title {
	display: flex;
	margin: 0 0 10px 0;
	div {
		flex: 1 1 0;
		p {
			font-size: 15px;
			color: #333;
		}
	}
}
.content {
	display: flex;
	.content_left {
		flex: 1 1 0;
		padding: 20px;
		margin: 0 10px 0 0;
		color: #333;
	}
	.content_right {
		flex: 1 1 0;
		padding: 20px;
		margin: 0 10px 0 0;
		color: #333;
	}
	.grey {
		background: #f7f8f9;
	}
	.green {
		background: #f6fbf9;
	}
}
/deep/.ant-collapse > .ant-collapse-item > .ant-collapse-header {
	color: #333;
	font-weight: 1000;
}


/deep/.d2h-file-wrapper {
  max-height: 500px;
  overflow-y: auto;
  overflow-x: hidden;
}

 /deep/.d2h-code-side-line{
  height:19px;
}

/deep/.d2h-file-side-diff {
	// height: 400px;
	// overflow: scroll;
	.hljs {
		height: auto;
	}
}

.ant-collapse-borderless > .ant-collapse-item {
	border: none;
}
.ant-collapse {
	background: #fff !important;
}
/deep/.ant-collapse-borderless > .ant-collapse-item > .ant-collapse-content {
	background: #fff !important;
}
</style>