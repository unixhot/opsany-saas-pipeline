/**
 * 前端版本检测
 *
 * 原理：构建时在 dist 根目录生成 version.json（仅含 buildTime），本模块周期性拉取并对比，
 * buildTime 变了就说明发布了新版本，再根据用户当前状态决定怎么处理。
 *
 * 三个核心时机的分工：
 * - 轮询（POLL_INTERVAL）：只在本标签页可见时运行，兜底"用户长时间停在同一个页面"的场景
 * - 空闲判定（IDLE_TIMEOUT）：判断"用户在本标签页但人已离开"，超过阈值就自动刷新、不弹窗打扰
 * - 隐藏延迟（HIDDEN_RELOAD_DELAY）：区分"短暂 alt-tab"和"真的离开"，真离开才在后台无感刷新
 *
 * 处理规则：
 * - 前台活跃：弹 Notification 提示手动刷新（同一版本只弹一次，防骚扰）
 * - 前台空闲 / 切后台：自动刷新，用户无感
 * - 多标签页：localStorage + storage 事件同步，一个标签页发现新版本，其他标签页也能感知
 */
import notification from 'ant-design-vue/es/notification'

// 轮询间隔：本标签页可见时，每隔 20s 拉一次 version.json 检测新版本。
// 为什么 20s：内部平台用户量小，20s 足够及时（部署后最多 20 秒内就能提示），
// 每次只是一个小 JSON 请求，负载可忽略；后台标签页会自动暂停轮询，不产生无效请求。
const POLL_INTERVAL = 20 * 1000

// 空闲判定：统计"本标签页内"最后一次用户操作（鼠标移动/点击/键盘/触屏）的时间，
// 若连续 3 分钟没有任何操作，认为用户暂时不在屏幕前（例如去开会、离开工位）。
// 此时若检测到新版本，直接自动刷新而不是弹窗，避免打扰。
const IDLE_TIMEOUT = 3 * 60 * 1000

// 切后台的刷新延迟：用户把本标签页切到后台（切到别的标签页/窗口/最小化）时启动计时。
// 10 秒后若页面【仍然】处于 hidden 状态（document.visibilityState === 'hidden'），
// 说明用户真的离开了，此时做一次后台检测，有新版本就在后台刷新完，
// 用户回来直接看到新版，全程无感。
// 若 10 秒内切回来了，说明只是短暂 alt-tab，取消计时器，走"可见 + 活跃 = 弹通知"的流程。
const HIDDEN_RELOAD_DELAY = 10 * 1000

// antdv Notification 的固定 key：同一 key 再次 open 会替换旧通知而不是叠加，
// 天然避免弹窗堆叠
const NOTIFICATION_KEY = 'app-version-update'

let checking = false // 并发锁：同一时刻只允许一个检测请求在飞，防止路由跳转+轮询同时触发
let lastBuildTime = null // 本标签页最近一次见到的版本（首次加载后不再为 null）
let notifiedBuildTime = null // 已弹过通知的版本，用于防重复：同一版本只弹一次
let pollTimer = null // 轮询定时器
let hiddenTimer = null // 切后台的 10 秒延迟计时器
let idleTimer = null // 空闲判定的定时器
let lastActivityTime = Date.now() // 本标签页内最后一次用户操作的时间
let isIdle = false // 是否处于空闲状态（人不在屏幕前）

/** 当前应用专属的 localStorage key，避免同源下多个 SaaS 互相覆盖 */
function getLocalStorageKey() {
    const segments = (window.location.pathname || '').split('/').filter(Boolean).slice(0, 2)
    return 'opsany_version_buildtime_' + (segments.join('_') || 'app')
}

/**
 * 从页面已有的 app 脚本标签反推静态资源基路径
 * 例如脚本 src 为 /o/workbench/static/js/runtime.xxx.js 时，返回 /o/workbench/static/
 * 部署形态：index.html 由 Django 渲染，静态资源与 version.json 都放在 static 目录下，
 * 因此 version.json 的地址 = 静态基路径 + 'version.json'
 * 这样不管部署在什么前缀路径下（/o/workbench/、/workbench/ 等）都能自动找到
 */
function getStaticBase() {
    const candidates = Array.prototype.slice.call(document.querySelectorAll('script[src]'))
    const script = candidates.find(function (s) {
        const src = s.getAttribute('src') || ''
        if (src.indexOf('static/js/') === -1 && src.indexOf('/js/') === -1) return false
        try {
            return new URL(src, window.location.href).origin === window.location.origin
        } catch (e) {
            return false
        }
    })
    if (script) {
        const pathname = new URL(script.getAttribute('src'), window.location.href).pathname
        const idx = pathname.lastIndexOf('/static/')
        if (idx > -1) {
            return pathname.slice(0, idx + '/static/'.length)
        }
    }
    return ''
}

/** 拉取最新 buildTime；拿不到返回 null（如本地开发没有 version.json，或接口异常） */
async function fetchBuildTime() {
    // ?t=时间戳 + cache:'no-store'：双重确保每次都能拿到最新的 version.json，不被浏览器缓存
    const url = getStaticBase() + 'version.json?t=' + Date.now()
    const res = await fetch(url, { cache: 'no-store' })
    if (!res.ok) return null
    const data = await res.json()
    return Number(data.buildTime) || null
}

function getLocalBuildTime() {
    try {
        const value = localStorage.getItem(getLocalStorageKey())
        return value ? Number(value) : null
    } catch (e) {
        // localStorage 不可用（隐私模式等）时返回 null，本标签页照常工作
        return null
    }
}

function saveLocalBuildTime(buildTime) {
    // 值有变化才写入，避免无意义的写操作触发其他标签页的 storage 事件
    if (buildTime !== getLocalBuildTime()) {
        try {
            localStorage.setItem(getLocalStorageKey(), String(buildTime))
        } catch (e) {
            // localStorage 不可用（隐私模式等）时静默忽略，本标签页照常工作
        }
    }
}

/** 刷新页面：location.reload() 前先清掉 localStorage，确保刷新后按新版本重新记录 */
function reloadPage() {
    try {
        localStorage.removeItem(getLocalStorageKey())
    } catch (e) {
        // localStorage 不可用（隐私模式等）时静默忽略，本标签页照常工作
    }
    window.location.reload()
}

/** 检测一次：与上次记录的版本对比，不一致则按当前状态分流处理 */
export async function checkVersion() {
    if (checking) return
    checking = true
    try {
        const buildTime = await fetchBuildTime()
        if (!buildTime) return
        if (lastBuildTime === null) {
            // 首次加载：只记录版本，不弹通知（用户打开的就是最新版，无需提示）
            lastBuildTime = buildTime
            saveLocalBuildTime(buildTime)
            return
        }
        if (buildTime !== lastBuildTime) {
            lastBuildTime = buildTime
            saveLocalBuildTime(buildTime)
            handleNewVersion(buildTime)
        }
    } catch (e) {
        // 网络异常/接口不可达/localStorage 不可用：静默跳过，等下次轮询或路由跳转再试
    } finally {
        checking = false
    }
}

/**
 * 发现新版本后的分流：
 * - 页面 hidden：交给隐藏逻辑（10 秒后台检查）处理，这里不弹也不刷
 * - 空闲（用户人不在屏幕前）：直接自动刷新，不打扰
 * - 活跃（用户正在操作）：弹通知，让用户自己决定什么时候刷新
 */
function handleNewVersion(buildTime) {
    if (document.visibilityState === 'hidden') return // 后台交给隐藏逻辑处理
    // 空闲直接自动刷新：即使本版本已弹过通知（被用户关掉了）也照样刷新，不打扰
    if (isIdle) {
        reloadPage()
        return
    }
    if (notifiedBuildTime === buildTime) return // 同一版本已弹过，不再重复弹
    notifiedBuildTime = buildTime // 先记录再弹，防止并发事件重复弹窗
    showNotification()
}

/**
 * antdv Notification：右上角提示 + "立即刷新"按钮
 * - key 固定：同一时间只保留一条通知，重复触发会替换而不是叠加
 * - duration 0：不自动消失，等用户自己决定（点刷新 / 点关闭）
 */
function showNotification() {
    notification.open({
        key: NOTIFICATION_KEY,
        message: '系统已更新',
        description: '检测到新版本，点击按钮立即刷新',
        duration: 0,
        btn: h => h(
            'a-button',
            {
                props: { type: 'primary', size: 'small' },
                on: { click: () => reloadPage() },
            },
            '立即刷新'
        ),
    })
}

/** 轮询：页面可见时运行，隐藏时暂停（后台用户看不到通知，轮询无意义还浪费请求） */
function startPolling() {
    stopPolling()
    pollTimer = setInterval(checkVersion, POLL_INTERVAL)
}

function stopPolling() {
    if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
    }
}

/** 空闲判定：监听本标签页内的用户操作，并定时检查是否超时 */
function initIdleDetect() {
    const markActivity = () => {
        lastActivityTime = Date.now()
        isIdle = false
    }
    ;['mousemove', 'mousedown', 'keydown', 'touchstart'].forEach(eventName => {
        window.addEventListener(eventName, markActivity, { passive: true })
    })
    // 每 30s 检查一次：距离最后一次操作超过 IDLE_TIMEOUT 就置为空闲。
    // 后台时该定时器会被浏览器节流，但空闲判定不依赖实时性，节流不影响结果
    idleTimer = setInterval(() => {
        if (Date.now() - lastActivityTime > IDLE_TIMEOUT) {
            isIdle = true
        }
    }, 30 * 1000)
}

/**
 * 页面隐藏/显示切换：
 * - 隐藏：停轮询 + 启动 10 秒计时器（10 秒后仍 hidden 说明真离开了，后台无感刷新）
 * - 显示：取消计时器 + 恢复轮询 + 立即检测一次（用户刚回来，马上知道有没有新版本）
 */
function initVisibilityChange() {
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            stopPolling()
            clearTimeout(hiddenTimer)
            hiddenTimer = setTimeout(async () => {
                // 10 秒后仍处于 hidden：用户确实离开了，检测一次，
                // 有新版本就在后台刷新完，用户回来直接看到新版
                try {
                    const buildTime = await fetchBuildTime()
                    if (buildTime && (lastBuildTime === null || buildTime !== lastBuildTime)) {
                        lastBuildTime = buildTime
                        saveLocalBuildTime(buildTime)
                        reloadPage()
                    }
                } catch (e) {
                    // 网络异常时静默跳过：等下次可见时再检测
                }
            }, HIDDEN_RELOAD_DELAY)
        } else {
            clearTimeout(hiddenTimer)
            startPolling()
            checkVersion()
        }
    })
}

/**
 * 多标签页同步：storage 事件只在【其他标签页】修改 localStorage 时触发。
 * 当某个标签页发现新版本并写入 localStorage 后，其他标签页会立刻感知，
 * 各自按自己的状态（活跃=弹窗 / 空闲=刷新 / 隐藏=交给隐藏逻辑）处理
 */
function initStorageSync() {
    window.addEventListener('storage', event => {
        if (event.key !== getLocalStorageKey()) return
        const buildTime = Number(event.newValue)
        if (!buildTime) return
        if (buildTime !== lastBuildTime) {
            // 页面在后台时不推进版本：交给"10 秒后台计时器"或"回前台立即检测"处理，
            // 否则后台标签页会静默漏更（既不在后台刷新，回来也不再提示）
            if (document.visibilityState === 'hidden') return
            lastBuildTime = buildTime
            handleNewVersion(buildTime)
        }
    })
}

/**
 * 初始化版本检测（幂等，重复调用不会重复注册）
 * @param {object} router vue-router 实例，注册路由跳转触发检测
 */
export function initVersionCheck(router) {
    // 仅生产环境开启；本地开发可用 VUE_APP_VERSION_CHECK=true 手动开启验证
    // （开发环境每次热更新 buildTime 都会变，默认开启会频繁弹窗打扰开发）
    const enabled = process.env.NODE_ENV === 'production' || process.env.VUE_APP_VERSION_CHECK === 'true'
    if (!enabled) return
    if (window.__VERSION_CHECK_INITED__) return
    window.__VERSION_CHECK_INITED__ = true

    initIdleDetect()
    initVisibilityChange()
    initStorageSync()
    startPolling()
    checkVersion()

    if (router) {
        // 路由跳转也触发一次检测：用户切页面时马上知道有没有新版本，不用等轮询
        router.afterEach(() => {
            checkVersion()
        })
    }
}
