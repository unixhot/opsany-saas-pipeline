/**
 * 消息状态图标工具
 * 通过 require.context 预加载 src/assets/message 下所有 png 图标，
 * 避免模板中 require(`${status}.png`) 在图片缺失时抛错。
 */
const messageStatusImageContext = require.context("../assets/message", false, /\.png$/)

const messageStatusImageMap = messageStatusImageContext.keys().reduce((map, key) => {
    const status = key.replace("./", "").replace(/\.png$/, "")
    map[status] = messageStatusImageContext(key)
    return map
}, {})

const defaultMessageStatusImage = messageStatusImageMap["default"] || messageStatusImageMap["1"] || ""

/**
 * 根据消息状态返回对应图标，本地无对应图标时回退到默认图标
 * @param { string | number } status 消息状态值
 */
export function getMessageStatusImage(status) {
    const key = String(status)
    return messageStatusImageMap[key] || defaultMessageStatusImage
}
