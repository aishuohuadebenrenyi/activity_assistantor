# Zentro 活动帮手 前端 (Activity Assistant Frontend)

本项目是基于 **uni-app x (UTS)** 开发的跨平台活动管理应用前端。

## 🚀 快速开始

1.  在 **HBuilderX** 中打开此目录 (`frontend/`)。
2.  **调试 App**: 运行 -> 运行到手机或模拟器。
3.  **调试小程序**: 运行 -> 运行到小程序模拟器 -> 微信开发者工具。

## ⚙️ 核心配置

配置文件位于 `utils/config.uts`:
- `USE_MOCK`: 全局 Mock 开关。开发环境下默认为 `true`，可快速体验全流程闭环。
- `BASE_URL`: 后端 API 基础路径。
- `CLEAR_CACHE_ON_START`: 调试用，开启后每次启动都会清除 `localStorage`，模拟首次登录。

## 🛠 技术架构

- **多端角色路由**: 通过 `pages.json` 条件编译实现。
  - `#ifdef MP-WEIXIN`: 默认为参与者视图。
  - `#ifndef MP-WEIXIN`: 默认为主办方管理视图。
- **UTS 状态管理**: 全局状态存储在 `store/index.uts`，支持跨页面响应式更新。
- **离线队列**: `utils/offline_queue.uts` 自动处理弱网环境下的数据同步。
- **Mock 拦截器**: `mock/index.uts` 完美模拟 RESTful API 响应。

## 📂 目录说明

- `pages/`: 页面组件 (.uvue)
- `store/`: UTS 响应式状态管理 (含 API 类型定义)
- `mock/`: 模拟数据与拦截逻辑
- `utils/`: 
  - `request.uts`: 网络请求封装 (集成 Mock & 离线队列)
  - `config.uts`: 全局环境配置
  - `offline_queue.uts`: 离线同步引擎
  - `analytics.uts`: 埋点统计封装
- `static/`: 静态资源 (图标、图片)
