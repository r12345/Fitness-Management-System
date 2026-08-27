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

前端通过 `/api` 请求后端接口，Vite 开发服务器已配置代理到 `http://127.0.0.1:8000`，对应 FastAPI 后端。

## 角色入口

- 超级管理员：`/dashboard`
- 前台运营：`/reception`
- 健身教练：`/coach`
- 普通会员：`/member`

演示账号：`admin`

演示密码：`123456`
