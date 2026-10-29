# AI 助手（扣子智能体）接入说明

全局右下角的悬浮球 AI 助手，基于扣子（Coze）Chat SDK 实现，支持**每个登录账号各自一份会话**。

---

## 一、一句话概述

前端直连扣子平台聊天，**后端只负责发令牌**。聊天消息不经过本项目后端，也不落库。

```
浏览器 ──①取令牌──> 你的后端 ──②JWT换token──> 扣子平台
   └──────────────③发消息（直连，不过后端）────────┘
```

---

## 二、文件清单

| 位置 | 职责 |
| --- | --- |
| `frontend/src/components/AgentFab.vue` | 右下角悬浮球。可拖动、吸附、跨页面常驻，挂在 `AppLayout.vue` 第 82 行 |
| `frontend/src/composables/useCozeAgent.js` | **核心**。懒加载 SDK、单例客户端、取令牌、过期刷新、销毁 |
| `frontend/src/api/agent.js` | 封装 `GET /agent/token` |
| `fitness_management/api/v1/agent.py` | 令牌接口，按 `user.id + user.role` 签发 |
| `fitness_management/core/coze.py` | 用 OAuth 私钥签 RS256 JWT → 换 access_token（带缓存） |
| `fitness_management/core/config.py` | 所有配置项，可用项目根 `.env` 覆盖 |
| `check_coze.py` | 自检脚本，一次性告诉你哪一步没通 |
| 项目根 `.env` / `.env.example` | OAuth 三件套配置（`.env` 已被 gitignore 忽略） |
| 项目根 `private_key.pem` | OAuth 应用私钥（已被 `*.pem` 规则忽略） |

路由里原来的 `/agent`「AI 助手」页面已删除 —— 它与全局悬浮球功能重复，且不承载任何业务。

---

## 三、会话隔离是怎么做到的

这是整套实现里唯一「非直觉」的部分。

### 问题：扣子把访问密钥本身当作使用者身份

Chat SDK 启动时会先调：

```
GET /v1/conversations?bot_id=..&connector_id=999&sort_field=updated_at&page_num=1&page_size=1
```

取「最近更新的那一条」会话，之后所有请求都打在这个 `conversation_id` 上。所以**所有人共用一个 PAT 时，扣子认为他们是同一个人**，B 打开对话框就能看到 A 刚说的话（实测确认）。

### 解法：OAuth JWT + session_name

官方文档「如何实现会话隔离」写明**仅 OAuth JWT 鉴权支持**，需在 JWT payload 里带 `session_name`（业务侧用户唯一标识）。官方 FAQ 特别说明 **userInfo 参数无效**（已实测过：4 组不同 uid 全部落在同一个 conversation_id 上）。

私钥不能进浏览器，所以签 JWT 这一环必须在后端。

| | 改之前 | 现在 |
| --- | --- | --- |
| 鉴权凭据 | 前端写死一个公共 PAT | 后端按登录用户签发专属令牌 |
| 扣子眼中的身份 | 所有人都是同一个人 | `gym-admin-1`、`gym-coach-2`、`gym-member-3`… |
| 会话 | 全部共用 conversation #1 | 每人一条独立会话 |

`session_name` 拼成「前缀 + 角色 + 用户 ID」。带角色有两个原因：

1. 排障时一眼看出是谁；
2. 库里 `sys_user.id` 与 `member.id` 是两套自增，只用数字的话「3 号员工」和「3 号会员」会被并成同一个人。

`session_name` 必须**恒定** —— 同一个用户每次算出同一个字符串，否则扣子每次都当他新访客，历史会话就断了。

---

## 四、一次点击的完整时序

**① 页面加载**
`AppLayout` 挂 `<AgentFab />`，此时**不加载任何 SDK 资源**。SDK 单文件约 13MB，而本项目构建产物才 1.5MB，绝不能拖慢首屏。悬浮球位置从 localStorage 恢复。

**② 鼠标悬停**
触发 `preloadAgent()`，静默拉 SDK + 建客户端。用户犹豫的一两秒里就加载完了，真点下去基本秒开。预取失败静默吞掉 —— 预取失败不该弹错误打扰人。

**③ 点击** → `openAgent()` → `ensureClient()`

```js
const token = await resolveAuthToken();          // 先拿令牌
client = new window.CozeWebSDK.WebChatClient({ config: { bot_id }, auth: { type: "token", token } });
```

**顺序不能反**：客户端构造时就把令牌和会话固定下来了，之后再换令牌无效。

**④ 后端签发**（`core/coze.py`）

```python
payload = {
    "iss": settings.COZE_OAUTH_APP_ID,
    "aud": "api.coze.cn",
    "iat": now,
    "exp": now + 600,                       # JWT 只活 10 分钟，够走完换取流程
    "jti": secrets.token_urlsafe(32),       # 防重放
    "session_name": session_name,           # ← 隔离的关键
}
jwt.encode(payload, 私钥, algorithm="RS256", headers={"kid": KID})
```

换来的 `access_token` 有效期由 `COZE_TOKEN_TTL_SECONDS` 决定（默认 7200 秒，扣子上限 86399）。后端按 `session_name` 缓存，剩余不足 2 分钟才重签。

> 坑：扣子返回的 `expires_in` 有时是「过期时间戳」而不是「剩余秒数」，代码两种都做了兼容。

**⑤ 令牌过期**
`onRefreshToken: () => resolveAuthToken(true)`。SDK 内部是 `await this.options.auth?.onRefreshToken?.call(...)`，所以返回 Promise 是安全的，能自动续期。

**⑥ 退出登录**
`AppLayout.vue` 第 277 行 `destroyAgent()`。**这行不能删**：客户端是单例，退出登录只是 `router.replace("/login")` 不刷新页面，不销毁的话换账号登进来，聊天窗里还挂着上一个人的令牌和对话记录。

---

## 五、关键实现细节

### 懒加载 + 单例 + 并发保护

SDK 没有「是否已初始化」的查询入口，重复 `new` 会叠出多个聊天窗。所以缓存的必须是**初始化 Promise 而不只是实例**：

```js
function ensureClient() {
  if (clientPromise) return clientPromise;   // 悬停预取与点击打开可能同时进来
  clientPromise = (async () => { ... })();
  clientPromise.catch(() => { clientPromise = null; });  // 失败要能重试
  return clientPromise;
}
```

失败时必须清掉缓存，否则用户会永久卡在失败态。

### 不用 SDK 自带的悬浮球

`ui.asstBtn.isNeed = false`。它固定在右下角、不能拖动、且只在进过「AI 助手」页之后才存在。自己写的 `AgentFab` 才能跨页面常驻、可拖动、能显示隔离状态。

### 降级链与状态显示

```
后端专属令牌 → 拿不到（没配 OAuth / 接口挂 / 未登录）→ 公共 PAT → 功能可用但不隔离
```

降级是**静默**发生的。前端用一个响应式 `authMode`（`unknown / isolated / shared`），把状态写进悬浮球气泡：

- `AI 助手 · 独立会话 · 按住可拖动`
- `AI 助手 · 共享会话 · 按住可拖动`

不显示的话，使用者会一直以为隔离是好的，直到某天看见别人的聊天记录才发现。

`useCozeAgent.js` 里的公共 PAT 是兜底用的，**写在前端等于公开**（DevTools → Network 谁都能看到，拿到后能调你账号下有权限的全部扣子接口）。隔离配好后建议移除，代价是后端不可用时助手直接打不开。

---

## 六、配置项

项目根 `.env`（从 `.env.example` 复制，已被 gitignore 忽略）：

| 变量 | 说明 |
| --- | --- |
| `COZE_OAUTH_APP_ID` | OAuth 应用 ID（JWT 的 `iss`） |
| `COZE_OAUTH_KID` | 公钥指纹（JWT header 的 `kid`） |
| `COZE_OAUTH_PRIVATE_KEY_PATH` | 私钥文件路径，相对路径按项目根解释 |
| `COZE_OAUTH_PRIVATE_KEY` | 可选。PEM 全文内联（换行写成 `\n`），适合从密钥管理服务注入 |
| `COZE_BOT_ID` | 智能体 ID |
| `COZE_TOKEN_URL` | 换取地址。个人版/企业标准版用默认值；企业旗舰版多组织场景才需覆盖 |
| `COZE_TOKEN_TTL_SECONDS` | 令牌有效期，默认 7200，上限 86399 |
| `COZE_SESSION_PREFIX` | session_name 前缀，默认 `gym-` |

**注意：配置是启动时读的，改完必须重启后端。**

### 修改指引

| 改什么 | 改哪里 |
| --- | --- |
| 换智能体 | 前端 `useCozeAgent.js:50` + 后端 `config.py` 的 `COZE_BOT_ID`（两处要一致） |
| 换模型 | **代码里没有**，去 coze.cn 智能体编排页改 |
| 换 SDK 版本/语种 | `useCozeAgent.js` 的 `SDK_URL`（当前 cn 包 1.2.0-beta.19） |
| 会话名前缀 | `.env` 的 `COZE_SESSION_PREFIX` |
| 令牌有效期 | `.env` 的 `COZE_TOKEN_TTL_SECONDS` |

---

## 七、常见坑

### 1. 发消息报 `code 4015`

症状：窗口能开、欢迎语也能显示（那些是 SDK 本地渲染的），一发消息就报
`has not been published to the channel Agent As API`。

原因：欢迎语不碰服务端，发消息要 `POST https://api.coze.cn/v3/chat`，服务端校验渠道绑定，没发布就直接拒。

解法：

```bash
curl -X POST https://api.coze.cn/v1/bot/publish \
  -H "Authorization: Bearer $COZE_PAT" -H "Content-Type: application/json" \
  -d '{"bot_id":"<你的BOT_ID>","connector_ids":["999"]}'
```

- 渠道 ID：ChatSDK=999、API=1024
- 想两条通路都通要**分成两次调**，一次传两个 ID 实测返回 code 0 但渠道不生效
- 发布**异步生效**，等 30~90 秒
- 在扣子后台重新编辑/发布智能体可能覆盖渠道绑定，需要重发一次

### 2. 改完后端没生效

前端 `src/api/request.js` 里写死了 `BASE_URL = http://127.0.0.1:8001/api/v1`，**没有读 `import.meta.env`**（`build.mjs` 传了 `configFile:false`，Vite 的 env 不生效），所以仓库根那个 `.env` 里的 `VITE_API_BASE_URL` 是死配置。

用户自己起的服务不带 `--reload`，改完后端**必须手动重启 8001**。

### 3. 自检时误判为「隔离没生效」

浏览器走查脚本注入的 `localStorage.token` 若是前一天签发的 → 401 → 前端正常降级到 PAT → 气泡显示「共享会话」，同时拿到空 `data`。**现象和「OAuth 没配好」一模一样**，很容易往错误方向排查。每次走查前先重新签发会话 token。

另外 `authMode` 是**异步**确定的：hover 只触发 `preloadAgent()`，它要拉 13MB SDK 并真的去换令牌，固定 `sleep 600ms` 一定读到 `unknown`，断言要轮询（最多 15 秒）。

浏览器里 fetch 后端是**跨域**的（dev 在 5173、后端在 8001），拿不到响应体，令牌比对要在 Node 侧发请求。

### 4. 配置看起来齐全但签 JWT 失败

只判断字符串非空的话，`.env` 里写了 `COZE_OAUTH_PRIVATE_KEY_PATH=private_key.pem` 而文件还没放上去时，状态是「配置齐全」，一路走到签 JWT 才炸在「读取扣子私钥失败」。

`is_configured()` 已改为**判文件是否存在**，缺失提示里直接打出解析后的绝对路径。

---

## 八、自检与验证

```bash
# ① 后端能不能签出令牌
.venv/Scripts/python.exe check_coze.py
#    → 看「两个用户拿到的是不同的令牌 —— 会话隔离已生效」

# ② 重启后端后各角色调接口
GET /api/v1/agent/token  →  enabled=true, session_name=gym-{role}-{uid}

# ③ 浏览器看气泡文案
#    hover 悬浮球 →「AI 助手 · 独立会话 · 按住可拖动」
```

走查脚本：`scripts/smoke_coze_isolation.js`（在 WorkBuddy 工作区，非项目内）。

### 当前状态（2026-09-22）

OAuth 三项已配好并实测生效，四角色各自拿到不同令牌：

| 角色 | session_name |
| --- | --- |
| 管理员 | `gym-admin-1` |
| 教练 | `gym-coach-2` |
| 会员 | `gym-member-3` |
| 前台 | `gym-reception-4` |

智能体信息：`健身系统问答助手`，模型 `豆包·2.0·pro`，bot_id 见 `.env`。

---

## 九、安全提醒

- `private_key.pem` 与 `.env` 已被 gitignore 忽略，提交前用 `git check-ignore -v private_key.pem .env` 确认。
- 私钥泄露 = 别人能冒充你的 OAuth 应用。
- 公共 PAT 是明文写在前端的兜底，隔离配好后建议移除。
