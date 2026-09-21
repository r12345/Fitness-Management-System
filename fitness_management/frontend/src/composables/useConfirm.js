import { reactive } from "vue";

// 全局只维护一份确认框状态。
// App.vue 里挂一个 <ConfirmDialog/>，任何页面调用 confirmDialog(...) 都复用它，
// 不必每个页面各写一套弹窗、也不用再弹浏览器原生的 confirm（那个样式无法统一）。
const state = reactive({
  visible: false,
  title: "",
  message: "",
  details: [], // [{ label, value }]，用于列出「课程 / 时间 / 地点」这类关键信息
  confirmText: "确定",
  cancelText: "取消",
  tone: "default" // default | danger
});

let resolver = null;

/**
 * 打开确认框，返回 Promise<boolean>：确定 true / 取消或关闭 false。
 *
 * 用法：
 *   const ok = await confirmDialog({ title: "删除课程", message: "…" });
 *   if (!ok) return;
 *   await doDelete();
 *
 * @param {object} options
 * @param {string}   options.title      标题
 * @param {string}   options.message    正文说明
 * @param {Array}    options.details    [{label, value}] 关键信息清单
 * @param {string}   options.confirmText 确认按钮文案
 * @param {string}   options.cancelText  取消按钮文案
 * @param {string}   options.tone        default | danger（danger 会把确认按钮变红）
 */
export function confirmDialog(options = {}) {
  const {
    title = "确认操作",
    message = "",
    details = [],
    confirmText = "确定",
    cancelText = "取消",
    tone = "default"
  } = options;

  // 上一个确认框还没处理就被新的顶掉时，把旧的按「取消」结掉，
  // 否则它那边的 await 会永远挂着，后面的代码就再也不执行了。
  if (resolver) {
    const stale = resolver;
    resolver = null;
    stale(false);
  }

  state.title = title;
  state.message = message;
  state.details = Array.isArray(details) ? details : [];
  state.confirmText = confirmText;
  state.cancelText = cancelText;
  state.tone = tone;
  state.visible = true;

  return new Promise(function (resolve) {
    resolver = resolve;
  });
}

/** 弹窗组件内部读取状态用 */
export function useConfirmState() {
  return state;
}

/** 弹窗组件内部收尾用：关闭并兑现 Promise */
export function settleConfirm(result) {
  state.visible = false;
  const done = resolver;
  resolver = null;
  if (done) done(result);
}
