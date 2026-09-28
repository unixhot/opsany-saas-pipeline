<template>
	<span v-if="userInfo.support_config">
		<a-dropdown class="support" :getPopupContainer="triggerNode => triggerNode" v-model="support_visible">
			<span class="support_label">
				<a-icon type="customer-service" class="support_label_icon"></a-icon>
				<span>支持</span>
				<a-icon :type="support_visible ? 'up' : 'down'" class="support_icon support_label_icon"></a-icon>
			</span>
			<a-menu slot="overlay" @click="clickMenu" class="custom_menu">
				<template v-for="(item, index) in support_list">
					<template v-if="item.show">
						<a-menu-item v-if="!item.divider && !item.is_version" class="menu_item" :key="index">
							<a-popover
								placement="left"
								v-if="item.tooltip"
								:title="null"
								:getPopupContainer="triggerNode => triggerNode"
								arrowPointAtCenter
								:mouseLeaveDelay="0.2"
							>
								<div slot="content" class="wechat_box">
									<img class="wechat_img" :src="item.tooltip_img" alt="" />
									<div>{{ item.tooltip_title }}</div>
								</div>
								<div class="contentbox">
									<a-icon :type="item.icon" class="icon"></a-icon>
									<span class="title">{{ item.title }}</span>
								</div>
							</a-popover>
							<div v-else class="contentbox">
								<a-icon v-if="item.icon" :type="item.icon" class="icon"></a-icon>
								<span class="title">{{ item.title }}</span>
							</div>
						</a-menu-item>
						<a-menu-item-group v-if="item.is_version" class="version_box">
							<span class="title" slot="title">{{ item.title }}</span>
						</a-menu-item-group>
						<a-menu-divider v-if="item.divider" style="margin-top:6px;margin-bottom: 8px" />
					</template>
				</template>
			</a-menu>
		</a-dropdown>
	</span>
</template>
<script>
import { mapState } from "vuex";
export default {
	data() {
		return {
			support_list_test: [
				{ title: "官方文档", icon: "file-text", url: "https://dev.opsany.cn/docs/", tooltip: false, is_version: false, show: true },
				{
					title: "获取支持", //展示名
					icon: "qrcode", //图标
					url: undefined, //链接地址
					tooltip: true, //是否显示tooltip
					tooltip_title: "微信扫码获取支持", //tooltip标题
					tooltip_img: "https://console.opsany.com/img/wechat.2aa53039.png", // 二维码图片地址
					show: true, //是否展示
				},
				{ title: "社区论坛", icon: "message", url: "https://www.srestack.com/", tooltip: false, show: true },
				{ divider: true, show: true }, //分割线
				{
					title: "提交反馈",
					icon: undefined,
					url: "https://dev.opsany.cn/t//workbench/#/feedback/addFeedBack?from_url=true",
					tooltip: false,
					show: true,
				},
				{
					title: "为OpsAny提交贡献",
					icon: undefined,
					url: "https://github.com/unixhot",
					tooltip: false,
					show: true,
				},
				{
					title: "社区支持版v2.2.2",
					icon: undefined,
					url: "https://dev.opsany.cn/t//workbench/#/feedback/addFeedBack?from_url=true",
					tooltip: false,
					is_version: true, //是否是版本号
					show: true,
				},
			],
			support_visible: false,
		};
	},
	computed: {
		...mapState({
			userInfo: state => state.user.userInfo || {},
		}),
		support_list() {
			return this.$store.state.user.userInfo?.support_config_list || [];
		},
	},
	methods: {
		clickMenu({ key }) {
			const item = this.support_list[key];
			if (!item.url) return;
			window.open(item.url);
		},
	},
	mounted() {},
};
</script>
<style scoped lang="less">
.support {
	margin-left: 14px;
	&_label {
		color: #fff;
		display: inline-block;
		height: 50px;
		line-height: 50px;
		cursor: pointer;

		&_icon {
			color: #fff;
			margin: 0 6px;
			transform: translateY(-1px);
			font-size: 12px;
		}
	}
}
.custom_menu {
	padding: 6px 0;
	.menu_item {
		display: flex;
		align-items: center;
		padding: 0;
		.contentbox {
			padding: 10px 18px;
			width: max-content;
			display: flex;
			align-items: center;
			.icon {
				color: #333333;
				margin-right: 8px;
			}
			.title {
				color: #333333;
			}
		}
		.wechat_box {
			margin: 0 auto;
			text-align: center;
			.wechat_img {
				margin-top: 2px;
				width: 92px;
				height: 92px;
			}
			> div {
				color: #666666;
				font-size: 12px;
				margin-top: 8px;
			}
		}
	}
	.version_box {
		margin: 4px 0 6px 0;
		cursor: default;
		.title {
			color: gray;
			font-size: 12px;
			padding-left: 6px;
			padding-bottom: 8px;
		}
	}
}
.ant-dropdown-menu {
	border-radius: 6px;
}
</style>
