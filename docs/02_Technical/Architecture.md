# 活动帮手 (Activity Assistant) 技术架构文档

## 1. 技术架构概览

### 1.1 前端架构
- **框架**：uni-app x (基于 Vue 3 + UTS)
- **编译模式**：纯原生渲染 (App-Nvue)，保障高性能体验。
- **路由策略**：使用 `pages.json` 的条件编译实现多端角色隔离。
- **状态管理**：Vue Reactivity (响应式 Store)，存储于 `store/index.uts`。
- **网络层**：
  - **请求拦截**：`request.uts` 统一处理 JWT 注入与 Mock 切换。
  - **离线机制**：`offline_queue.uts` 实现非 GET 请求的本地持久化队列，断网自动入队，恢复自动重试。
  - **Mock 拦截**：`mock/index.uts` 模拟 RESTful API 行为，支持内存状态更新。

### 1.2 后端架构
- **开发语言**：Python 3.9+
- **Web 框架**：Flask
- **数据库**：MySQL / SQLite (通过 SQLAlchemy ORM)
- **核心模块**：
  - **Auth**: JWT 签发与校验、验证码缓存、微信 OpenID 获取。
  - **Activity**: 内容安全校验 (WeChat SecCheck)、活动管理接口。
  - **Participant**: CSV 导出逻辑、报名与签到核销逻辑。

## 2. 数据与安全

- **用户认证**：基于 JWT (HS256) 的身份验证，Token 有效期 7 天。
- **数据安全**：
  - 微信小程序端强制使用内容安全校验接口。
  - 报名名单导出采用 CSV 异步模拟发送模式。
- **离线同步**：请求队列采用 FIFO 顺序，确保数据一致性。
- **传输安全**：推荐生产环境配置全站 HTTPS。

## 3. 核心交互流程

### 3.1 扫码签到流程 (Participant & Organizer)
1.  **参与者**: 打开“报名凭证”页，前端根据 `registration_id` 生成 Base64 编码的签到码。
2.  **组织者**: 在“报名人员”页点击扫码，解析码内容。
3.  **核销**: 发送 `POST /checkin` 请求。若成功，本地 Store 同步更新 `checkinRecords` 并重新计算签到率。

### 3.2 离线同步流程
1.  用户提交修改 -> 网络不可用 -> `request.uts` 将请求元数据存入 `localStorage`。
2.  监听 `onNetworkStatusChange` -> 状态变为 Online -> 触发 `processQueue()`。
3.  遍历队列重发请求 -> 成功后移除 -> 提示“数据同步完成”。
