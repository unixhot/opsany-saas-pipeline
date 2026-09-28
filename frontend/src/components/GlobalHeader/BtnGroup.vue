<template>
	<div class="content">
		<a :href="otherAppUrl + 'bastion/#/console/console'" target="_blank" v-if="userInfo.console_config">
			<a-button type="link" class="a-button"><a-icon class="icon-color" type="desktop"></a-icon>控制台</a-button>
		</a>
		<a :href="otherAppUrl + 'workbench/#/'" v-if="userInfo.workbench_config">
			<a-button type="link" class="a-button"><a-icon class="icon-color" type="home"></a-icon>工作台</a-button>
		</a>

		<a-dropdown class="message" v-if="userInfo.message_config">
			<span>
				<a-icon class="icon-color message_icon" type="bell"></a-icon>
				<span style="margin-left: 5px">消息</span>
				<span v-if="count" class="badge">{{ count }}</span>
			</span>
			<div slot="overlay" class="message_content">
				<div class="header">
					<div class="header_title">系统消息</div>
					<a class="header_right" :href="otherAppUrl + 'workbench/#/msgCenter/subscriptionSetting'">消息接收管理</a>
				</div>
				<a-spin :spinning="loading">
					<div v-if="msgList.length" style="background: #ffffff">
						<div class="desc" v-for="item in msgList" :key="item.id" @click="linkToMsgDesc(item.id)">
							<div class="desc_title">
								<a-badge color="green" v-if="!item.is_read" />
								<a-badge status="default" v-else />
								{{ item.message.title_one }}
							</div>
							<div class="desc_time">
								<span>{{ item.message.create_time.split(".")[0] }}</span>
								<a-tooltip
									v-if="item.message.message_status"
									:title="
										(message_status_list.find(it => it.key == item.message.message_status) &&
											message_status_list.find(it => it.key == item.message.message_status).value) ||
										''
									">
									<img :src="getMsgStatusImg(item.message.message_status)" alt="" />
								</a-tooltip>
							</div>
						</div>
						<div class="more">
							<a :href="otherAppUrl + 'workbench/#/msgCenter/messageManage'">
								<a-button v-if="showMore" type="link">查看更多</a-button>
							</a>
							<a-button type="link" @click="readAll">全部已读</a-button>
						</div>
					</div>
					<a-empty v-else style="padding: 20px 0; margin: 0; background: #ffffff" />
				</a-spin>
			</div>
		</a-dropdown>

		<Support></Support>

	</div>
</template>
<script>
import { getUserMessageList, readAllMessage } from "@/api/messageManage";
import { mapState } from "vuex";
import Support from "./Support.vue";
import { getMessageStatusImage } from "@/utils/messageStatus";
export default {
	components: {
		Support,
	},
	data() {
		return {
			url: window.API_ROOT.split("/")[0],
			otherAppUrl: window.API_ROOT.replace("/pipeline", ""),
			showMore: false,
			loading: false,
			msgList: [],
			count: 0,
			message_status_list: [
				{ key: 1, value: "成功" },
				{ key: 2, value: "失败" },
				{ key: 3, value: "正在执行" },
				{ key: 4, value: "任务终止" },
				{ key: 5, value: "等待执行" },
				{ key: 6, value: "工单待办" },
				{ key: 7, value: "工单状态变更" },
				{ key: 8, value: "工单结束" },
				{ key: 9, value: "告警" },
				{ key: 10, value: "告警恢复" },
				{ key: 11, value: "告警关闭" },
				{ key: 12, value: "告警认领" },
				{ key: 13, value: "资源过期" },
				{ key: 14, value: "部分失败" },
			],
			intervalMessage: null,
		};
	},
	watch: {
		"userInfo.message_config": function(val) {
			if (!val) {
				clearInterval(this.intervalMessage);
			}
		},
	},
	methods: {
		getMsgStatusImg(status) {
			return getMessageStatusImage(status);
		},
		readAll() {
			readAllMessage().then(res => {
				this.getMsgData();
			});
		},
		getMsgData() {
			this.loading = true;
			const params = {
				current: 1,
				pageSize: 5,
			};
			getUserMessageList(params)
				.then(res => {
					this.msgList = res.data.message_list;
					this.count = res.data.not_read_count > 99 ? 99 + "+" : res.data.not_read_count;
					this.showMore = res.data.all_count > 5;
				})
				.finally(() => {
					this.loading = false;
				});
		},
		linkToMsgDesc(id) {
			const url = this.otherAppUrl + `workbench/#/msgCenter/messageManage/messageManageDesc?id=${id}`;
			window.location.href = url;
		},
	},
	mounted() {
		this.getMsgData();
		this.intervalMessage = setInterval(() => {
			this.getMsgData();
		}, 1000 * 30);
	},
	computed: {
		...mapState({
			userInfo: state => state.user.userInfo || {},
		}),
	},
};
</script>
<style scoped lang="less">
.content {
	color: #fff;
	button {
		border: none !important;
		color: #fff;
	}
	.icon-color {
		color: #fff;
		transform: translateY(-1px);
	}
	.message {
		display: inline-block;
		position: relative;
		min-width: 80px;
		text-align: center;
		.message_icon {
			transform: translateY(-1.5px);
		}
	}
	.badge {
		display: inline-block;
		padding: 1px 2px;
		min-width: 16px;
		min-height: 15px;
		line-height: 15px;
		text-align: center;
		background-color: #ff9900;
		color: #ffffff;
		border-radius: 50%;
		position: absolute;
		top: 4px;
		right: 0px;
		font-size: 10px;
	}
}

.message_content {
	width: 350px;
	min-height: 100px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 10px;
		border-bottom: 1px solid #eeeeee;
		background: #fafafa;
		&_title {
			font-weight: bold;
		}
		&_right {
			color: #0099ff;
			cursor: pointer;
		}
	}
	.desc {
		width: 100%;
		padding: 8px 10px;
		cursor: pointer;
		&:hover {
			background-color: #eeeeee;
		}
		div {
			overflow: hidden;
			word-break: break-all;
			white-space: nowrap;
			text-overflow: ellipsis;
		}
		&_title {
			color: #333333;
		}
		&_time {
			font-size: 14px;
			color: #666666;
			display: flex;
			justify-content: space-between;
			align-items: center;
			img {
				width: 16px;
				height: 16px;
				margin-right: 2px;
			}
		}
		&:not(:last-child) {
			border-bottom: 1px solid #eeeeee;
		}
	}
	.more {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 15px 10px;
		color: @primary-color;
	}
}
</style>
