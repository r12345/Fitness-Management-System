# 健身管理系统 Vue3 前端

## 技术栈

- Vue3
- Vue Router
- Vite
- ECharts

## 启动方式

```bash
npm install
npm run dev
```

开发服务器默认地址：`http://localhost:5173/`

如果当前环境无法写入系统 npm 缓存，可执行：

```bash
npm install --cache .npm-cache
```

## 构建

```bash
npm run build
```

构建产物输出到 `dist/`。

## 前后端分离

前端请求地址在 `src/api/request.js` 里，默认 `http://127.0.0.1:8001/api/v1`
（可用 `.env` 的 `VITE_API_BASE_URL` 覆盖），与后端 `main.py` 启动的端口一致。
`dev.mjs` 里的 `/api` 代理同样指向 8001，仅作备用入口。

## 角色入口

- 超级管理员：`/dashboard`
- 前台运营：`/reception`
- 健身教练：`/coach`
- 普通会员：`/member`

演示账号以数据库 `sys_user.username` 为准（如「超级管理员」「教练」「会员」「前台」），
登录时还需选择与账号 `role` 一致的角色，否则会被判定为「密码错误或身份错误」。
仓库里不含任何明文密码。
