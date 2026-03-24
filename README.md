# Zentro

Zentro 是一款基于 **uni-app x (UTS)** 和 **Python Flask** 开发的全栈活动管理应用。本项目采用前后端分离架构，前端运行在 iOS/Android 平台，后端部署于阿里云函数计算 (FC)。

## 📚 项目简介

本应用旨在帮助活动组织者高效管理活动全流程，同时为参与者提供便捷的报名与签到体验。

### 🎭 角色分工与平台适配
本项目采用 **一套代码，多端适配** 的策略，通过条件编译实现角色隔离：
- **App 端 (iOS/Android)**: 面向 **活动主办方**。功能包括活动创建、报名管理、扫码/手动核销、数据导出及统计。
- **微信小程序端**: 面向 **普通参与者**。功能包括浏览活动、在线报名、查看电子票（签到码）、自助签到。

---

## 🛠 技术栈

### 前端 (Frontend)
- **框架**: [uni-app x](https://uniapp.dcloud.net.cn/uni-app-x/) (Vue 3 + UTS)
- **核心能力**:
  - **原生渲染**: 纯原生组件渲染，提供丝滑的列表滚动与交互体验。
  - **离线优先**: 内置离线请求队列 (`offline_queue.uts`)，支持弱网/断网环境下操作自动同步。
  - **Mock 机制**: 完善的 Mock 拦截器 (`mock/index.uts`)，支持脱离后端进行全流程闭环调试。

### 后端 (Backend)
- **语言**: Python 3.9+
- **框架**: Flask 3.0 + SQLAlchemy
- **安全**: JWT 鉴权、微信内容安全校验 (SecCheck)、数据传输加密。
- **功能**: RESTful API、CSV 报名名单导出、验证码发送 (SMS)。

---

## 🚀 快速开始

### 1. 环境准备

确保您的开发环境已安装以下工具：
- [HBuilderX](https://www.dcloud.io/hbuilderx.html) (App 开发版，建议 4.0+)
- [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html) (调试小程序)
- [Python 3.9+](https://www.python.org/)

### 2. 后端启动 (Backend)
```bash
# 1. 进入项目根目录
cd activity_assistant_v6

# 2. 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖并启动
pip install -r backend/requirements.txt
python run.py
```
> **成功提示**: 终端显示 `Running on http://0.0.0.0:9000` 即表示启动成功。

### 3. 前端启动 (Frontend)

1.  在 **HBuilderX** 中打开 `frontend` 目录。
2.  **调试 App**: 运行 -> 运行到手机或模拟器。
3.  **调试小程序**: 运行 -> 运行到小程序模拟器 -> 微信开发者工具。

---

## 🔌 配置说明

### 网络与 Mock
配置文件位于 `frontend/utils/config.uts`:
- `USE_MOCK`: `true` (默认) 使用本地 Mock 数据；`false` 连接 `BASE_URL` 指定的后端。
- `BASE_URL`: 后端 API 地址。真机调试请使用局域网 IP。

### 微信小程序 AppID
在 `frontend/manifest.json` 中配置您的 `appid` 以启用微信登录和分享功能。

---

## 📂 目录结构

```
activity_assistant_v6/
├── backend/            # 后端代码 (Python Flask)
│   ├── routes/         # 业务路由 (活动、报名、鉴权)
│   ├── services/       # 外部服务 (微信 SDK, 短信服务)
│   └── models.py       # 数据库模型
├── frontend/           # 前端代码 (uni-app x)
│   ├── pages/          # 页面文件 (.uvue)
│   ├── store/          # UTS 响应式状态管理
│   ├── mock/           # Mock 数据及拦截逻辑
│   └── utils/          # 离线队列、网络请求封装
├── docs/               # 项目全量文档 (PRD, 架构, 接口)
└── run.py              # 后端启动入口
```
