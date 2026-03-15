# 代码结构梳理与审查索引

> **Version**: v6.2.0 | **Last Updated**: 2026-03-15

本文档用于把“代码—接口—数据—功能—文档”之间的映射关系固化下来，方便后续持续迭代时做到：
- 新增/修改接口时，同步更新 API 文档与错误码；
- 新增/修改数据模型时，同步更新数据库设计文档；
- 关键业务流程调整时，同步更新架构与功能说明；
- 通过 Git 版本管理追踪文档与代码的同版本变化。

## 1. 代码目录与职责

### 1.1 后端（Flask + SQLAlchemy）

- 入口与应用工厂：[backend/app.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/app.py)
  - 创建 Flask app、加载配置、初始化扩展（DB/CORS/限流/安全头）
  - 注册所有 Blueprint（`/api/...`）
  - 注入 Request-ID、统一异常转 API 错误响应
- 数据模型（ORM）：[backend/models.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/models.py)
  - 用户/活动/报名/签到/举报
  - 幂等键、组织与团队、计费与权益、客服会话、埋点事件与指标
- 路由层（业务 API）：[backend/routes](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/routes)
  - 认证：[auth.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/routes/auth.py)
  - 活动：[activity.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/routes/activity.py)
  - 参与者/导出：[participant.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/routes/participant.py)
  - 用户/注销/举报：[user.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/routes/user.py)
  - 组织与成员：[org.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/routes/org.py)
  - 套餐/订阅/权益：[billing.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/routes/billing.py)
  - 客服入口/会话记录：[support.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/routes/support.py)
  - 埋点上报/看板：[analytics.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/routes/analytics.py)
- 服务封装（外部依赖适配）：[backend/services](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/services)
  - 短信：[sms_service.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/services/sms_service.py)
  - 微信能力：[wechat_service.py](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/services/wechat_service.py)
- 通用工具（鉴权/幂等/错误/链路追踪）：[backend/utils](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/backend/utils)

### 1.2 前端（uni-app x / UTS / uvue）

- 应用入口：[frontend/main.uts](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/main.uts)、[frontend/App.uvue](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/App.uvue)
- 页面路由：[frontend/pages.json](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/pages.json)
- 页面实现：[frontend/pages](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/pages)
- 组件：[frontend/components](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/components)
- 网络与离线能力（关键）：[frontend/utils/request.uts](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/utils/request.uts)、[frontend/utils/offline_queue.uts](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/utils/offline_queue.uts)
- 埋点与分析（关键）：[frontend/utils/analytics.uts](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/utils/analytics.uts)
- 平台适配（外链/平台识别）：[frontend/adapters/platform.uts](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/adapters/platform.uts)

## 2. 关键业务流程索引

### 2.1 登录与鉴权

- 前端：`request.uts` 从本地 `user_data` 读取 token，注入 `Authorization: Bearer ...`。
- 后端：`auth_required` 解码 JWT，注入 `request.user` 供业务层使用。

### 2.2 断网写入与重放（离线队列）

- 前端：非 GET 且离线时写入本地队列；网络恢复后 FIFO 重放。
- 后端：写接口统一支持 `Idempotency-Key`，避免重放造成重复写入。

### 2.3 活动报名与签到核销

- 报名：`POST /api/activities/<id>/register`
- 票据：`GET /api/activities/<id>/my-ticket` 返回 Base64 签到码
- 核销：`POST /api/activities/<id>/checkin` 支持二维码或 registration_id

### 2.4 用户注销（冷静期）

- `DELETE /api/user/account`：
  - 第一次请求进入 `pending_deletion` 冷静期；
  - 冷静期内再次请求执行不可逆脱敏与关联数据清理。

### 2.5 埋点与看板

- 前端：本地缓冲（存储）+ 批量上报（最多 20 条/批），并跳过 401 自动跳转以避免登录循环。
- 后端：`POST /api/analytics/events/batch` 支持匿名上报（可选 token 解析并关联 user/org）。

## 3. 文档同步清单（后续更新入口）

- API 文档：[API_Reference.md](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/docs/02_Technical/API_Reference.md)
- 架构文档：[Architecture.md](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/docs/02_Technical/Architecture.md)
- 数据库设计（将新增）：`docs/02_Technical/Database_Design.md`
- 错误码规范（将新增）：`docs/02_Technical/Error_Codes.md`
- 文档版本管理（将新增）：`docs/02_Technical/Documentation_Versioning.md`

