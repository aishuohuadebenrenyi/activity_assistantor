# 活动帮手 (Activity Assistant) 技术架构文档

> **Version**: v6.2.0 | **Last Updated**: 2026-03-23

## 1. 修订历史

| 版本号 | 修订日期 | 修订人 | 修订内容说明 |
| :--- | :--- | :--- | :--- |
| v6.1.0 | 2026-03-10 | Dev Team | 初始架构文档 |
| v6.2.0 | 2026-03-15 | AI Assistant | 增加组织租户、计费订阅及埋点分析架构说明 |
| v6.2.1 | 2026-03-23 | AI Assistant | 增加 FC 部署架构、短信服务、Redis 存储说明 |

## 2. 技术架构概览

### 2.1 前端架构
- **框架**：uni-app x (基于 Vue 3 + UTS)
- **编译模式**：纯原生渲染 (App-Nvue)，保障高性能体验。
- **路由策略**：使用 `pages.json` 的条件编译实现多端角色隔离。
- **状态管理**：Vue Reactivity (响应式 Store)，存储于 `store/index.uts`。
- **网络层**：
  - **请求拦截**：`request.uts` 统一处理 JWT 注入与 Mock 切换。
  - **离线机制**：`offline_queue.uts` 实现非 GET 请求的本地持久化队列，断网自动入队，恢复自动重试。
  - **Mock 拦截**：`mock/index.uts` 模拟 RESTful API 行为，支持内存状态更新。

### 2.2 后端架构
- **开发语言**：Python 3.9+
- **Web 框架**：Flask 3.0.0
- **数据库**：SQLite (开发) / 阿里云 RDS MySQL (生产)
- **缓存**：内存 (开发) / 阿里云 Redis (生产)
- **部署平台**：阿里云函数计算 (FC)
- **核心模块**：
  - **Auth**: JWT 签发与校验、验证码缓存、微信 OpenID 获取。
  - **Activity**: 内容安全校验 (WeChat SecCheck)、活动管理接口。
  - **Org & Billing**: 基于组织 ID 的多租户逻辑、套餐权益控制。
  - **Analytics**: 异步批量埋点上报、日维度指标聚合任务。
  - **Support**: 外部客服系统集成、会话上下文 Token 机制。

## 3. 数据与安全

### 3.1 幂等性保障
- **前端**：为所有非 GET 请求生成唯一 `Idempotency-Key`。
- **后端**：使用 `IdempotencyKey` 表记录 24 小时内的请求快照，防止重复处理。

### 3.2 用户认证
- 基于 JWT (HS256) 的身份验证，Token 有效期 7 天。

### 3.3 数据安全
- 微信小程序端强制使用内容安全校验接口。
- 报名名单导出采用 CSV 异步模拟发送模式。
- 手机号脱敏显示。

### 3.4 离线同步
- 请求队列采用 FIFO 顺序，确保数据一致性。

### 3.5 传输安全
- 推荐生产环境配置全站 HTTPS。

## 4. 核心交互流程

### 4.1 扫码签到流程 (Participant & Organizer)
1. **参与者**: 打开"报名凭证"页，前端根据 `registration_id` 生成 Base64 编码的签到码。
2. **组织者**: 在"报名人员"页点击扫码，解析码内容。
3. **核销**: 发送 `POST /checkin` 请求。若成功，本地 Store 同步更新 `checkinRecords` 并重新计算签到率。

### 4.2 离线同步流程
1. 用户提交修改 -> 网络不可用 -> `request.uts` 将请求元数据存入 `localStorage`。
2. 监听 `onNetworkStatusChange` -> 状态变为 Online -> 触发 `processQueue()`。
3. 遍历队列重发请求 -> 成功后移除 -> 提示"数据同步完成"。

## 5. 阿里云函数计算部署

### 5.1 部署架构
```
客户端 (uni-app x)
       │
       ▼ HTTPS
阿里云 API 网关
       │
       ▼ 触发器
阿里云函数计算 (FC)
       │
       ├─► 阿里云 RDS MySQL
       ├─► 阿里云 Redis
       └─► 阿里云 SLS (日志)
```

### 5.2 关键配置
| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| 内存规格 | 512MB - 1024MB | 根据并发量调整 |
| 执行超时 | 30s | API 响应时间上限 |
| 单实例并发 | 10 | 减少实例创建开销 |
| 预留实例 | 1 | 避免冷启动延迟 |
| VPC 配置 | 与 RDS 同 VPC | 内网访问数据库 |

### 5.3 相关文件
- `backend/fc_handler.py`: FC 入口函数
- `backend/s.yaml`: Serverless Devs 部署配置

## 6. 第三方服务集成

### 6.1 微信开放平台
- **登录**: 通过 code 换取 openid
- **内容安全**: msgSecCheck 文本审核
- **小程序码**: 生成活动二维码

### 6.2 阿里云短信
- **验证码发送**: 支持 Mock/生产双模式
- **配置项**: ALIYUN_SMS_ACCESS_KEY_ID, ALIYUN_SMS_ACCESS_KEY_SECRET

### 6.3 Redis 缓存
- **验证码存储**: 支持 Redis/内存双模式
- **限流计数**: Flask-Limiter 存储后端
- **配置项**: REDIS_URL
