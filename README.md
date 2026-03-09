# 活动帮手 (Activity Assistant)

活动帮手是一款基于 **uni-app x (UTS)** 和 **Python Flask** 开发的全栈活动管理应用。本项目采用前后端分离架构，前端运行在 iOS/Android 平台，后端部署于阿里云函数计算 (FC)。

## 📚 项目简介

本应用旨在帮助活动组织者高效管理活动全流程，包括活动发布、报名管理、扫码签到、数据统计等功能。

- **前端**: `frontend/` - 基于 uni-app x (UTS) 开发，纯原生渲染。
- **后端**: `backend/` - 基于 Python Flask 开发，RESTful API 风格。
- **文档**: `docs/` - 包含产品说明、需求文档及用户手册。

---

## 🛠 技术栈

### 前端 (Frontend)
- **框架**: uni-app x (Vue 3 + UTS)
- **开发工具**: HBuilderX 4.0+
- **目标平台**: iOS, Android

### 后端 (Backend)
- **语言**: Python 3.9+
- **框架**: Flask 3.0
- **数据库**: MySQL 8.0 (开发环境可选 SQLite)
- **ORM**: SQLAlchemy

---

## 🚀 快速开始

### 1. 环境准备

确保您的开发环境已安装以下工具：
- [HBuilderX](https://www.dcloud.io/hbuilderx.html) (App 开发版)
- [Python 3.9+](https://www.python.org/)
- [Git](https://git-scm.com/)

### 2. 后端启动 (Backend)

后端服务运行在 `backend/` 目录下。

#### macOS / Linux
```bash
# 1. 进入项目根目录
cd activity_assistant_v6

# 2. 创建虚拟环境
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 安装依赖
pip install -r backend/requirements.txt

# 5. 启动服务
python run.py
```

#### Windows
```powershell
# 1. 进入项目根目录
cd activity_assistant_v6

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
venv\Scripts\activate

# 4. 安装依赖
pip install -r backend/requirements.txt

# 5. 启动服务
python run.py
```

> **成功提示**: 终端显示 `Running on http://0.0.0.0:9000` 即表示启动成功。

#### 6. 生成测试数据 (可选)
如果需要填充测试数据（活动、报名、签到等），可运行：
```bash
python seed.py
```

### 3. 前端启动 (Frontend)

前端项目位于 `frontend/` 目录下。

1.  打开 **HBuilderX**。
2.  点击菜单栏 **文件** -> **打开目录**，选择本项目下的 `frontend` 文件夹。
3.  找到 `pages/activities/activities.uvue` 或任意页面文件。
4.  点击顶部工具栏的 **运行** 按钮：
    - 选择 **运行到内置浏览器** (快速预览 UI)。
    - 或选择 **运行到手机或模拟器** (体验原生性能)。
    - **注意**: 若需调试 App 端，请确保已配置好 iOS/Android 基座。

---

## 🔌 前后端联调配置

默认情况下，前端使用 Mock 数据。若要连接本地后端：

1.  确保后端服务已启动 (默认端口 `9000`)。
2.  修改前端网络请求配置 (通常在 `store/index.uts` 或 API 配置文件中)：
    ```typescript
    // 示例：将 Base URL 指向本地
    const BASE_URL = "http://localhost:9000/api";
    ```
3.  确保手机/模拟器与电脑处于同一局域网，并将 `localhost` 替换为电脑的局域网 IP 地址 (如 `192.168.1.x`)。

---

## ☁️ 部署说明

### 后端部署 (阿里云 FC)
本项目适配阿里云 Web 函数 (Serverless)。
1.  在阿里云控制台创建 **函数计算** 服务。
2.  配置运行环境为 **Python 3.9**。
3.  上传 `backend/` 目录代码。
4.  配置启动命令为 `python run.py`。
5.  设置环境变量 (如数据库连接串)。

### 前端发布
1.  在 HBuilderX 中点击 **发行** -> **原生App-云打包**。
2.  配置 App 图标、启动图及证书。
3.  打包生成 `.ipa` (iOS) 或 `.apk` (Android)。

---

## 📂 目录结构

```
activity_assistant_v6/
├── backend/            # 后端代码 (Python Flask)
│   ├── routes/         # API 路由
│   ├── models.py       # 数据库模型
│   ├── config.py       # 配置文件
│   └── ...
├── frontend/           # 前端代码 (uni-app x)
│   ├── pages/          # 页面文件 (.uvue)
│   ├── static/         # 静态资源
│   ├── store/          # 状态管理
│   └── ...
├── docs/               # 项目文档
│   ├── PRODUCT_DESC.md # 产品说明
│   ├── REQUIREMENTS.md # 需求文档
│   └── USER_MANUAL.md  # 用户手册
├── run.py              # 后端启动脚本
└── README.md           # 全局项目说明
```
