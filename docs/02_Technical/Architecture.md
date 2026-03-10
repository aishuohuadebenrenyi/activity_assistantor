# 活动帮手 (Activity Assistant) 技术架构文档

## 1. 技术架构概览

### 1.1 前端架构
- **框架**：uni-app x (基于 Vue 3 + UTS)
- **编译模式**：纯原生渲染 (App-Nvue)，保障高性能体验。
- **状态管理**：Vue Reactivity (Pinia 风格)。
- **网络层**：
  - 封装 `request.uts` 处理全局拦截与错误。
  - 实现离线队列 (`offline_queue.uts`)，支持断网操作并在网络恢复后自动同步。

### 1.2 后端架构
- **运行环境**：阿里云 Web 函数 (Serverless FC)
- **开发语言**：Python 3.9+
- **Web 框架**：Flask
- **数据库**：MySQL (RDS)
- **API 规范**：RESTful API

## 2. 数据与安全

- **数据存储**：云端持久化存储，支持多端同步。
- **用户认证**：基于 JWT (JSON Web Token) 的身份验证。
- **隐私保护**：手机号等敏感信息加密存储。
- **传输安全**：全站强制 HTTPS。

## 3. 目录结构说明

### 前端 (frontend/)
- `pages/`: 页面组件
- `components/`: 通用 UI 组件
- `utils/`: 工具函数 (请求、分析、配置)
- `store/`: 全局状态管理
- `static/`: 静态资源

### 后端 (backend/)
- `routes/`: API 路由定义
- `models.py`: 数据库模型
- `app.py`: 应用入口
