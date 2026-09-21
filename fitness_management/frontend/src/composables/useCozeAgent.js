/**
 * 扣子（Coze）智能体接入。
 *
 * 做五件事：
 * 1. **懒加载**：Chat SDK 单文件约 13MB，首次进入「AI 助手」页（或点悬浮球 / 悬停悬浮球）
 *    时才注入 <script>，不让它拖慢首屏 —— 这个项目自己的构建产物才 1.5MB，再挂 13MB 不能接受。
 * 2. **单例 + 并发保护**：整个应用只 new 一个 WebChatClient。SDK 没有「是否已初始化」的
 *    查询入口，重复 init 会叠出多个聊天窗，只能自己记住；而且「悬停预取」与「点击打开」
 *    可能同时触发，所以缓存的必须是 Promise 而不只是实例。
 * 3. **不自带悬浮球**：`ui.asstBtn.isNeed = false`。入口统一由 AppLayout 里的
 *    `<AgentFab>` 负责 —— 那个球才能在**所有页面**常驻、并且可以拖动。
 * 4. **聊天窗常驻**：不 destroy。点开一次后，切到别的页面它还在。
 * 5. **会话隔离**：优先用后端签发的「用户专属令牌」，拿不到才退回 PAT（见下）。
 *
 * 智能体信息（用你的令牌调 GET https://api.coze.cn/v1/bots/{id} 核对过）：
 *   name        = 健身系统问答助手
 *   description = 可以回答一些健身相关的问题
 *   model       = 豆包·2.0·pro
 *
 * ⚠️ 前置条件一：**智能体必须发布到「Chat SDK」渠道，否则发消息必失败。**
 *   症状：窗口能打开、欢迎语也能显示（那些是 SDK 本地渲染的），但一发消息就报
 *        code 4015 / "has not been published to the channel Agent As API"。
 *   原因：欢迎语不碰服务端，发消息要 POST https://api.coze.cn/v3/chat，
 *        服务端校验渠道绑定，没发布就直接拒。
 *   解法（一条 curl，token 用你自己的 PAT）：
 *        curl -X POST https://api.coze.cn/v1/bot/publish \
 *          -H "Authorization: Bearer $COZE_PAT" -H "Content-Type: application/json" \
 *          -d '{"bot_id":"7687570944927531048","connector_ids":["999"]}'
 *        渠道 ID：ChatSDK=999、API=1024。想两条通路都通就**分成两次调**，
 *        实测一次传 ["1024","999"] 返回 code 0 但渠道没生效，分开调才成功。
 *        发布是**异步生效**的，等 30~90 秒再发消息。
 *   注意：在扣子后台重新编辑/发布这个智能体，可能覆盖掉渠道绑定，需要重发一次。
 *
 * ⚠️ 前置条件二：**会话隔离必须用 OAuth JWT，PAT 做不到。**
 *   扣子把「访问密钥」本身当作使用者身份。用同一个 PAT 鉴权时所有访客在扣子眼里是
 *   同一个人，共享同一份会话记录 —— SDK 启动先调
 *        GET /v1/conversations?...&sort_field=updated_at&page_num=1&page_size=1
 *   取「最近更新的那一条」，所以 B 打开对话框就能看到 A 刚说的话（实测确认）。
 *   官方文档「如何实现会话隔离」写明**仅 OAuth JWT 支持**，要在 JWT 的 payload 里带
 *   `session_name`（业务侧用户 UID）；官方 FAQ 还特别说明 **userInfo 参数无效**
 *   （我也实测过，4 组不同 uid 全都落在同一个 conversation_id 上）。
 *   所以：令牌由后端 `GET /api/v1/agent/token` 签发（私钥不能进浏览器），
 *   本文件负责取用与过期刷新；后端没配置时自动退回 PAT，功能可用但不隔离。
 */

import { get_agent_token } from "../api/agent";

/** 智能体 ID：扣子开发页 URL 里 `bot` 参数后的数字。这里取自你给的店铺页地址。 */
export const COZE_BOT_ID = "7687570944927531048";

/**
 * 个人访问令牌（PAT）。
 *
 * ⚠️ 写在前端就等于公开：任何人打开 DevTools → Network 都能看到它，
 * 拿到后能调用你账号下有权限的全部扣子接口。
 * 这是扣子官方「安装代码」的默认做法（它自己生成的代码就是把 token 明文贴进页面），
 * 自己用的演示项目没问题；**要对外发布必须改成后端代理换 token**，别让令牌出到浏览器。
 *
 * ⚠️ 另外它还是**会话不隔离的根因**：扣子用它来认人，所有人共用一个 PAT
 *   就等于共用一份对话记录。所以下面优先走后端签发的专属令牌，
 *   只有当后端没配置 OAuth 时才退回到它。
 */
const COZE_PAT = "pat_JXDYiq9gB81gAjFECJm5KMjvfCjoiEo7VykcCSeOdZOuXUcYCV3ElkD0YO6VEP9u";

/** 中文包。SDK 有 cn 与非 cn 两套，业务是中文就用 cn，否则内置文案是英文。 */
const SDK_URL =
  "https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.19/libs/cn/index.js";

export const AGENT_NAME = "健身系统问答助手";
export const AGENT_DESC = "可以回答一些健身相关的问题";

/** 模块级单例：script 的 Promise 与 client 的 Promise 各一个 */
let scriptPromise = null;
let clientPromise = null;
/** 已就绪的实例，供 closeAgent / destroyAgent 同步取用 */
let client = null;

/** 令牌缓存：避免每次打开都往后端跑一趟；提前 60 秒作废，防止边界上拿到刚过期的 */
let authCache = { token: "", expiresAt: 0, isolated: false };
/** 令牌获取的并发保护：预取和点击可能同时进来，别打两次接口 */
let authPromise = null;

/**
 * 取这次要用的扣子令牌。
 *
 * 优先向后端要「当前登录用户专属」的令牌（带 session_name，可实现会话隔离）；
 * 后端没配 OAuth、未登录、或接口挂了，都退回公共 PAT —— 功能照常，只是会话不隔离。
 *
 * @param {boolean} force 忽略缓存强制重取（SDK 的 onRefreshToken 用）
 * @returns {Promise<string>} 可直接作为 Chat SDK `auth.token` 的字符串
 */
async function resolveAuthToken(force = false) {
  const now = Date.now();
  if (!force && authCache.token && authCache.expiresAt - now > 60000) {
    return authCache.token;
  }
  if (authPromise) return authPromise;

  authPromise = (async () => {
    try {
      const res = await get_agent_token();
      const data = (res && res.data) || {};
      if (data.enabled && data.token) {
        authCache = {
          token: data.token,
          expiresAt: Date.now() + Number(data.expires_in || 900) * 1000,
          isolated: true
        };
        return authCache.token;
      }
      // 后端在，只是没配 OAuth：这是可预期的降级，用 info 而不是报错
      console.info(
        "[AI助手] 未启用会话隔离，本次使用公共令牌。原因：",
        data.reason || "后端未返回 token"
      );
    } catch (err) {
      // 未登录 / 后端没起 / 网络异常，同样降级，不该因此让助手打不开
      console.warn("[AI助手] 获取专属令牌失败，回退公共令牌：", (err && err.message) || err);
    }
    authCache = {
      token: COZE_PAT,
      // 公共令牌没有有效期概念，给个 10 分钟缓存，好在换了配置后能自动重试
      expiresAt: Date.now() + 600000,
      isolated: false
    };
    return COZE_PAT;
  })();

  try {
    return await authPromise;
  } finally {
    authPromise = null;
  }
}

/** 当前是否拿到了会话隔离令牌（后端配好 OAuth 之后才为 true） */
export function isAgentIsolated() {
  return authCache.isolated;
}

/**
 * 注入 SDK script，只注入一次。
 * 失败时清掉 scriptPromise，让用户重试时能重新加载，而不是永久卡在失败态。
 */
function loadScript() {
  if (scriptPromise) return scriptPromise;
  scriptPromise = new Promise((resolve, reject) => {
    if (document.querySelector('script[data-coze-sdk="1"]')) {
      resolve();
      return;
    }
    const el = document.createElement("script");
    el.src = SDK_URL;
    el.async = true;
    el.dataset.cozeSdk = "1";
    el.onload = () => resolve();
    el.onerror = () => {
      scriptPromise = null;
      reject(new Error("Chat SDK 加载失败，请确认网络能访问 lf-cdn.coze.cn"));
    };
    document.head.appendChild(el);
  });
  return scriptPromise;
}

/**
 * 初始化客户端（幂等 + 并发安全）。
 *
 * 缓存的必须是**初始化 Promise**：悬停预取和点击打开可能在 SDK 还没加载完时同时进来，
 * 只判断 `if (client) return client` 两条线都会走到 `new`，结果叠出两个聊天窗。
 */
function ensureClient() {
  if (clientPromise) return clientPromise;
  clientPromise = (async () => {
    if (!window.CozeWebSDK) {
      await loadScript();
    }
    if (!window.CozeWebSDK || !window.CozeWebSDK.WebChatClient) {
      scriptPromise = null;
      clientPromise = null;
      throw new Error("Chat SDK 没挂到 window 上，可能被广告拦截插件拦了脚本");
    }
    // 先拿令牌再建实例：会话隔离靠的就是这里 —— 令牌不同，扣子认出来的人就不同
    const token = await resolveAuthToken();
    client = new window.CozeWebSDK.WebChatClient({
      config: {
        bot_id: COZE_BOT_ID
      },
      /*
       * 令牌鉴权。
       * onRefreshToken 是 SDK 要求的回调，SDK 内部会 `await` 它的返回值
       * （打包产物里是 `let e = await this.options.auth?.onRefreshToken?.call(...)`），
       * 所以这里可以放心返回 Promise —— 专属令牌只有 2 小时，过期得能自动续。
       */
      auth: {
        type: "token",
        token,
        onRefreshToken: () => resolveAuthToken(true)
      },
      componentProps: {
        title: AGENT_NAME,
        lang: "zh-CN",
        layout: "pc",
        width: 400,
        // 侧栏 z-index 是 30、toast-banner 是 200，聊天窗抬到 1200 保证在最上层
        zIndex: 1200
      },
      ui: {
        /*
         * 关掉 SDK 自带的右下角悬浮球。
         * 它固定在右下角、不能拖动、且只在「已经进过 AI 助手页」之后才存在，
         * 入口改由 AppLayout 里的自定义悬浮球统一提供（可拖、跨页面常驻）。
         */
        asstBtn: { isNeed: false },
        header: { isShow: true, isNeedClose: true },
        chatBot: { title: AGENT_NAME, width: 400 },
        base: { layout: "pc", lang: "zh-CN", zIndex: 1200 }
      }
    });
    return client;
  })();
  // 初始化失败要能让用户重试，不要把失败状态永久缓存下来
  clientPromise.catch(() => {
    clientPromise = null;
  });
  return clientPromise;
}

export function useCozeAgent() {
  /**
   * 打开智能体对话窗。首次调用会先加载 SDK（约 13MB，会有等待）。
   * @returns {Promise<void>} 失败时抛出带中文提示的 Error
   */
  async function openAgent() {
    const c = await ensureClient();
    c.showChatBot();
  }

  /** 收起对话窗（不销毁客户端） */
  function closeAgent() {
    if (client) client.hideChatBot();
  }

  /**
   * 只预热、不打开：把 13MB 的 SDK 提前拉下来并建好客户端。
   * 挂在悬浮球的 mouseenter 上，用户犹豫的那一两秒就加载完了，
   * 真点下去时基本是秒开。失败静默吞掉 —— 预取失败不该打扰用户。
   */
  function preloadAgent() {
    return ensureClient().catch(() => null);
  }

  /** 客户端是否已经就绪（用于展示加载状态） */
  function isAgentReady() {
    return Boolean(client);
  }

  /**
   * 销毁客户端，下次打开时重建。
   *
   * ⚠️ **退出登录时必须调**：客户端是单例、且构造时就把令牌和会话固定下来了。
   * 退出登录只是 `router.replace("/login")`（不刷新页面），如果不销毁，
   * 换个账号登进来后聊天窗里还挂着**上一个人的令牌和对话记录** —— 正好是我们要修的漏洞。
   */
  function destroyAgent() {
    if (client && typeof client.destroy === "function") client.destroy();
    client = null;
    clientPromise = null;
    // 令牌是按用户签的，也必须一起作废，否则新用户会用到旧用户的令牌
    authCache = { token: "", expiresAt: 0, isolated: false };
    authPromise = null;
  }

  return {
    openAgent,
    closeAgent,
    preloadAgent,
    isAgentReady,
    isAgentIsolated,
    destroyAgent,
    agentName: AGENT_NAME,
    agentDesc: AGENT_DESC,
    agentId: COZE_BOT_ID
  };
}
