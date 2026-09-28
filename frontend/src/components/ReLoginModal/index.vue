<template>
	<a-modal :visible="visible" :maskClosable="false" :keyboard="false" :footer="null" width="500px" @cancel="handleCloseToLogin">
		<div class="relogin_content">
			<div class="relogin_header">
				<a-icon type="info-circle" theme="filled" class="relogin_icon" />
				<div class="relogin_title">当前登录已超时,请不要关闭此窗口。</div>
			</div>
			<div class="relogin_desc">请点击"新窗口登录"完成登录，登录后点击"已完成登录"即可恢复当前页面。如未恢复请刷新页面。</div>
			<div class="relogin_btn_wrap">
				<a-button type="primary" @click="handleNewWindowLogin">新窗口登录</a-button>
				<a-button style="margin-left: 12px" @click="handleReload">已完成登录</a-button>
			</div>
		</div>
	</a-modal>
</template>

<script>
// 登录态失效弹窗：组件自监听 auth-failed 事件触发弹窗（挂在 App.vue 根组件，任何路由状态都可用）
// 页面内去重：visible 已 true 时忽略后续触发（轮询接口会持续返回 40100，避免重复弹窗）
// 恢复：监听"登录完成"广播（storage 事件 + BroadcastChannel），收到即刷新页面带新 cookie 恢复
import { getLoginUrl } from "@/utils/request";
export default {
	name: "ReLoginModal",
	data() {
		return {
			visible: false, // 弹窗显示状态，同时充当页面内去重标记
			bc: null, // BroadcastChannel 实例
			hasReload: false, // 防止重复导航（reload 或跳转登录页）
		};
	},
	mounted() {
		// 挂载即注册监听：auth-failed（弹窗触发）+ storage/BroadcastChannel（登录完成恢复），不依赖弹窗是否显示
		this.registerListener();
		// 兜底：40100 广播早于本组件挂载（如 token 失效后刷新白屏，main.js 已记录标记）→ 补弹
		if (window.__opsany_relogin_pending) {
			window.__opsany_relogin_pending = false;
			this.handleAuthFailed();
		}
	},
	methods: {
		// auth-failed 事件入口（组件自监听，幂等去重）
		onAuthFailed() {
			this.handleAuthFailed();
		},
		// 40100 入口：页面内去重，弹窗已显示则忽略（轮询每秒 40100 不会重复弹窗）
		handleAuthFailed() {
			if (this.visible || this.hasReload) return;
			this.visible = true;
		},
		// 新窗口打开登录页，原页面保持不丢
		handleNewWindowLogin() {
			window.open(getLoginUrl(), "_blank");
		},
		// 点击右上角 X 关闭：跳转登录页（当前页跳转，与"新窗口登录"区分；c_url 回跳可恢复）
		handleCloseToLogin() {
			if (this.hasReload) return;
			this.hasReload = true;
			window.location.href = getLoginUrl();
		},
		// 手动确认已完成登录：刷新页面（带新 cookie 重新拉数据），最稳
		handleReload() {
			if (this.hasReload) return;
			this.hasReload = true;
			window.location.reload();
		},
		// 注册监听：auth-failed 事件（弹窗触发）+ storage/BroadcastChannel（登录完成恢复）
		registerListener() {
			window.addEventListener("opsany-header:auth-failed", this.onAuthFailed);
			window.addEventListener("storage", this.onStorageChange);
			try {
				this.bc = new BroadcastChannel("opsany_relogin");
				this.bc.onmessage = e => {
					if (e.data === "login-complete") this.handleReload();
				};
			} catch (e) {
				/* 不支持 BroadcastChannel 时仅靠 storage 事件 */
			}
		},
		unregisterListener() {
			window.removeEventListener("opsany-header:auth-failed", this.onAuthFailed);
			window.removeEventListener("storage", this.onStorageChange);
			try {
				this.bc && this.bc.close();
			} catch (e) {}
			this.bc = null;
		},
		onStorageChange(e) {
			// storage 事件只在其他标签页写入时触发：登录页写了"登录完成"标记 → 立即恢复
			if (e.key === "opsany_relogin_flag" && e.newValue) {
				this.handleReload();
			}
		},
	},
	beforeDestroy() {
		this.unregisterListener();
	},
};
</script>

<style lang="less" scoped>
.relogin_content {
	padding: 10px 4px;
}
.relogin_header {
	display: flex;
	align-items: center;
	margin-bottom: 12px;
	.relogin_icon {
		font-size: 16px;
		color: #faad14;
		margin-right: 10px;
	}
	.relogin_title {
		font-size: 16px;
		font-weight: 500;
	}
}

.relogin_desc {
	font-size: 13px;
	color: #999;
	line-height: 1.6;
	margin-bottom: 20px;
	margin-left: 26px;
}
.relogin_btn_wrap {
	display: flex;
	justify-content: flex-end;
}
</style>
