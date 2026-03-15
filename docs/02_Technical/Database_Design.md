# 数据库设计文档 (Database Design)

> **Version**: v6.2.0 | **Last Updated**: 2026-03-15

## 1. 修订历史

| 版本号 | 修订日期 | 修订人 | 修订内容说明 |
| :--- | :--- | :--- | :--- |
| v6.1.0 | 2026-03-10 | Dev Team | 初始数据库设计，定义核心业务表 |
| v6.2.0 | 2026-03-15 | AI Assistant | 细化组织、订阅、埋点及客服相关表结构设计 |

## 2. 实体关系图 (ERD) 简述

- **用户 (User)** 与 **活动 (Activity)**: 一对多 (1:N)。一个用户可以创建多个活动。
- **活动 (Activity)** 与 **报名 (Registration)**: 一对多 (1:N)。一个活动可以有多个报名。
- **报名 (Registration)** 与 **签到 (CheckinRecord)**: 一对一 (1:1)。一个报名对应一个签到。
- **用户 (User)** 与 **组织 (Org)**: 一对一 (1:1)。当前逻辑下，每个用户默认拥有一个组织（作为 Owner）。
- **组织 (Org)** 与 **订阅 (Subscription)**: 一对多 (1:N)。记录组织随时间变化的订阅历史。
- **套餐 (Plan)** 与 **权益 (Entitlement)**: 多对多 (M:N)。通过 `PlanEntitlement` 关联。

## 2. 表结构详细定义

### 2.1 用户表 (`users`)
存储用户核心身份与状态。

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | Integer | PK | 自增 ID |
| phone | String(20) | Unique, Index | 手机号（登录凭证） |
| openid | String(128) | Unique, Index | 微信 OpenID |
| username | String(64) | - | 昵称 |
| avatar_url | String(255) | - | 头像 URL |
| bio | Text | - | 个人简介 |
| is_certified | Boolean | Default(False) | 是否实名认证 |
| status | String(20) | Default('active') | active/pending_deletion/deleted |
| created_at | DateTime | - | 创建时间 |
| deletion_requested_at | DateTime | - | 注销冷静期开始时间 |

### 2.2 活动表 (`activities`)
存储活动的核心配置与统计。

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | Integer | PK | 自增 ID |
| user_id | Integer | FK(users.id) | 组织者 ID |
| name | String(128) | Not Null | 活动名称 |
| type | String(50) | - | 类型（会议/展览等） |
| start_time | DateTime | Not Null | 开始时间 |
| location | String(255) | - | 地点 |
| description | Text | - | 详情描述 |
| capacity | Integer | Default(0) | 人数上限（0 为不限） |
| status | String(20) | Default('upcoming') | upcoming/ongoing/ended |
| views_count | Integer | Default(0) | 浏览量统计 |

### 2.3 报名表 (`registrations`)
记录用户的参与意向。

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | Integer | PK | 自增 ID |
| activity_id | Integer | FK(activities.id) | 所属活动 ID |
| name | String(64) | Not Null | 报名人姓名 |
| phone | String(20) | Not Null | 报名人电话 |
| created_at | DateTime | - | 报名时间 |

### 2.4 签到记录表 (`checkin_records`)
记录实际到场核销信息。

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | Integer | PK | 自增 ID |
| registration_id | Integer | FK, Unique | 关联报名 ID |
| activity_id | Integer | FK | 关联活动 ID (冗余) |
| checkin_time | DateTime | - | 签到时间 |
| device_info | String(255) | - | 设备指纹 |

### 2.5 组织表 (`orgs`)
支撑团队协作与计费的租户模型。

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | Integer | PK | 自增 ID |
| owner_user_id | Integer | FK, Unique | 拥有者 ID |
| name | String(128) | - | 组织名称 |
| status | String(20) | - | active/inactive |

### 3.6 订阅与计费相关表
- **套餐定义表 (`plans`)**
  | 字段名 | 类型 | 说明 |
  | :--- | :--- | :--- |
  | id | Integer | PK |
  | code | String(32) | 套餐代码（如 free, pro, enterprise） |
  | name | String(64) | 展示名称 |
  | price | Float | 价格 |
  | period_days | Integer | 有效周期（天） |
  | status | String(20) | active/archived |

- **权益定义表 (`entitlements`)**
  | 字段名 | 类型 | 说明 |
  | :--- | :--- | :--- |
  | key | String(64) | PK, 权益标识（如 export.enabled） |
  | name | String(64) | 权益描述 |
  | value_type | String(20) | boolean/integer |

- **订阅记录表 (`subscriptions`)**
  | 字段名 | 类型 | 说明 |
  | :--- | :--- | :--- |
  | id | Integer | PK |
  | org_id | Integer | FK(orgs.id) |
  | plan_id | Integer | FK(plans.id) |
  | status | String(20) | active/expired/cancelled |
  | start_at | DateTime | 开始时间 |
  | end_at | DateTime | 到期时间 |

### 3.7 辅助与运维表
- **幂等记录表 (`idempotency_keys`)**
  | 字段名 | 类型 | 说明 |
  | :--- | :--- | :--- |
  | key | String(128) | PK, 客户端生成的唯一 Key |
  | user_id | Integer | FK, 发起用户 |
  | request_hash | String(64) | 请求指纹 (Method+Path+Body) |
  | response_body | Text | 序列化的响应主体 |
  | response_status| Integer | 响应 HTTP 状态码 |
  | created_at | DateTime | 创建时间 (用于过期清理) |

- **埋点事件表 (`event_logs`)**
  | 字段名 | 类型 | 说明 |
  | :--- | :--- | :--- |
  | id | BigInt | PK |
  | event_name | String(64) | 事件名 |
  | user_id | Integer | 可选，触发用户 |
  | properties | JSON | 事件属性键值对 |
  | created_at | DateTime | 触发时间 |

- **客服会话表 (`support_sessions`)**
  | 字段名 | 类型 | 说明 |
  | :--- | :--- | :--- |
  | id | Integer | PK |
  | user_id | Integer | 发起用户 |
  | platform | String(20) | 来源平台 (ios/mp_weixin/h5) |
  | status | String(20) | opened/closed |
  | opened_at | DateTime | 开启时间 |

## 4. 索引设计原则
- 唯一索引：`users.phone`, `users.openid`, `idempotency_keys.key`, `orgs.owner_user_id`。
- 业务查询索引：`activities.status`, `event_logs.event_name`, `metrics_daily.date`。
- 外键索引：所有 `_id` 结尾的关联字段均建立索引以优化 Join 性能。
