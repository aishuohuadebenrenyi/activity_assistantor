# Zentro 项目技术文档

> **Version**: v1.0.0 | **Last Updated**: 2026-03-26

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [目录结构](#3-目录结构)
4. [后端模块详解](#4-后端模块详解)
5. [前端模块详解](#5-前端模块详解)
6. [数据库设计](#6-数据库设计)
7. [API 接口定义](#7-api-接口定义)
8. [用户交互流程](#8-用户交互流程)
9. [数据流向](#9-数据流向)
10. [离线机制](#10-离线机制)
11. [安全机制](#11-安全机制)
12. [部署说明](#12-部署说明)
13. [相关文档](#13-相关文档)

---## 1. 项目概述

### 1.1 产品定位

**Zentro** 是一款面向活动组织者的移动端活动管理应用，采用 **uni-app x** 跨平台框架开发，支持 iOS、Android 和微信小程序三端运行。

### 1.2 核心功能

| 功能模块 | 描述 |
|---------|------|
| 活动管理 | 创建、编辑、删除、查看活动 |
| 报名管理 | 用户报名、取消报名、报名名单查看 |
| 签到管理 | 扫码签到、手动签到、签到记录管理 |
| 数据导出 | 报名名单 CSV 导出并发送邮件 |
| 用户中心 | 个人资料管理、账号注销 |

### 1.3 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端框架 | uni-app x (UTS) |
| 后端框架 | Python Flask |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 缓存 | Redis (验证码/限流) |
| 认证 | JWT (7天有效期) |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层 (Client)                         │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   iOS App       │  Android App    │     微信小程序               │
│  (主办方/管理员) │  (主办方/管理员) │     (参与者/用户)            │
└────────┬────────┴────────┬────────┴──────────────┬──────────────┘
         │                 │                       │
         └─────────────────┼───────────────────────┘
                          │
                    ┌─────▼─────┐
                    │  API 网关  │
                    │  (Flask)  │
                    └─────┬─────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
   ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
   │  Auth     │    │ Activity  │    │  User     │
   │  Module   │    │  Module   │    │  Module   │
   └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
        ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
        │  SQLite/  │ │ Redis │ │ 第三方服务 │
        │ PostgreSQL│ │       │ │ (微信/短信) │
        └───────────┘ └───────┘ └───────────┘
```

### 2.2 多端策略

| 平台 | 角色 | TabBar 配置 | 核心功能 |
|------|------|-------------|----------|
| iOS/Android App | 主办方/管理员 | 首页 \| 创建 \| 我的 | 活动管理、扫码核销、数据导出 |
| 微信小程序 | 参与者/用户 | 我的报名 \| 个人中心 | 浏览活动、报名、查看电子票 |

---

## 3. 目录结构

```
Zentro/
├── backend/                      # 后端代码
│   ├── routes/                   # API 路由模块
│   │   ├── auth.py              # 认证接口 (登录/注册/验证码)
│   │   ├── activity.py          # 活动接口 (CRUD/分享/签到)
│   │   ├── participant.py       # 参与者接口 (报名/导出)
│   │   ├── user.py              # 用户接口 (资料/注销/举报)
│   │   ├── org.py               # 组织接口 (团队管理)
│   │   ├── billing.py           # 计费接口 (订阅/权益)
│   │   ├── analytics.py         # 埋点接口 (事件上报)
│   │   └── support.py           # 客服接口 (会话管理)
│   ├── services/                 # 业务服务层
│   │   ├── wechat_service.py    # 微信服务 (内容安全/登录)
│   │   ├── sms_service.py       # 短信服务 (验证码发送)
│   │   ├── email_service.py     # 邮件服务 (导出发送)
│   │   └── qrcode_service.py    # 二维码服务 (签到码生成)
│   ├── utils/                    # 工具函数
│   │   ├── auth.py              # 鉴权装饰器
│   │   ├── errors.py            # 错误响应格式化
│   │   ├── idempotency.py       # 幂等性控制
│   │   └── request_id.py        # 请求链路追踪
│   ├── models.py                 # 数据模型定义
│   ├── app.py                    # Flask 应用入口
│   └── config.py                 # 配置管理
│
├── frontend/                     # 前端代码
│   ├── pages/                    # 页面组件
│   │   ├── activities/          # 首页 (活动列表)
│   │   ├── activity/            # 活动相关页面
│   │   │   ├── create/          # 创建活动
│   │   │   ├── detail/          # 活动详情
│   │   │   ├── participants/    # 报名/签到管理
│   │   │   ├── share/           # 分享活动
│   │   │   ├── success/         # 创建成功
│   │   │   └── ticket/          # 报名凭证
│   │   ├── auth/                # 登录页面
│   │   ├── profile/             # 个人中心
│   │   ├── user/                # 用户活动列表
│   │   └── about/               # 关于页面
│   ├── components/               # 公共组件
│   │   ├── ActivityItem.uvue    # 活动卡片组件
│   │   ├── ActivitySkeleton.uvue# 骨架屏组件
│   │   ├── ParticipantItem.uvue # 参与者列表项
│   │   └── StatCard.uvue        # 统计卡片
│   ├── store/                    # 状态管理
│   │   ├── index.uts            # 全局 Store (活动/用户状态)
│   │   └── types.uts            # 类型定义
│   ├── utils/                    # 工具函数
│   │   ├── request.uts          # 网络请求封装
│   │   ├── config.uts           # 配置管理
│   │   ├── offline_queue.uts    # 离线队列
│   │   ├── id_mapping.uts       # 临时ID映射
│   │   ├── idempotency.uts      # 幂等键生成
│   │   ├── analytics.uts        # 埋点上报
│   │   └── network_state.uts    # 网络状态
│   ├── mock/                     # Mock 数据
│   │   ├── data.uts             # 模拟数据定义
│   │   └── index.uts            # Mock 拦截器
│   ├── App.uvue                  # 应用入口
│   ├── pages.json                # 页面路由配置
│   └── manifest.json             # 应用配置
│
└── docs/                         # 文档目录
    ├── 01_Product/              # 产品文档
    ├── 02_Technical/            # 技术文档
    └── 07_Legal/                # 法律文档
```

---

## 4. 后端模块详解

### 4.1 认证模块 (auth.py)

**路由前缀**: `/api/auth`

| 接口 | 方法 | 描述 |
|------|------|------|
| `/send-code` | POST | 发送短信验证码 (60秒频率限制) |
| `/login` | POST | 手机号验证码登录 (自动注册) |
| `/login/wechat` | POST | 微信登录 (code 换取 openid) |
| `/login/apple` | POST | Apple 登录 (iOS 强制要求) |

**验证码存储策略**:
- 生产环境: Redis (支持 TTL 和多进程共享)
- 开发环境: 内存字典 (无需 Redis)

**JWT Token 有效期**: 7 天

### 4.2 活动模块 (activity.py)

**路由前缀**: `/api/activities`

| 接口 | 方法 | 描述 | 权限 |
|------|------|------|------|
| `/` | GET | 获取活动列表 (支持分页/筛选) | 公开 |
| `/` | POST | 创建活动 | 需登录 |
| `/<id>` | GET | 获取活动详情 (浏览量+1) | 公开 |
| `/<id>` | PUT | 更新活动 | 仅组织者 |
| `/<id>` | DELETE | 删除活动 (级联删除报名/签到) | 仅组织者 |
| `/<id>/share` | GET | 获取分享信息 (URL Link/小程序码) | 公开 |
| `/<id>/my-ticket` | GET | 获取我的报名凭证 | 需登录 |
| `/<id>/checkin` | POST | 扫码签到 | 仅组织者 |
| `/<id>/report` | POST | 举报活动 | 需登录 |

**内容安全**: 创建/更新活动时调用微信 msgSecCheck 接口校验

### 4.3 参与者模块 (participant.py)

**路由前缀**: `/api/activities`

| 接口 | 方法 | 描述 | 权限 |
|------|------|------|------|
| `/<id>/participants` | GET | 获取报名名单 | 仅组织者 |
| `/<id>/register` | POST | 报名活动 | 需登录 |
| `/<id>/register` | DELETE | 取消报名 | 需登录 |
| `/<id>/export` | POST | 导出报名名单 (CSV 邮件发送) | 仅组织者 |
| `/<id>/checkin/<reg_id>` | DELETE | 取消签到 | 仅组织者 |

### 4.4 用户模块 (user.py)

**路由前缀**: `/api/user`

| 接口 | 方法 | 描述 | 权限 |
|------|------|------|------|
| `/profile` | GET | 获取个人资料 | 需登录 |
| `/profile` | PUT | 更新个人资料 | 需登录 |
| `/account` | DELETE | 注销账号 (15天冷静期) | 需登录 |
| `/report` | POST | 举报内容 | 需登录 |
| `/registrations` | GET | 获取我的报名列表 | 需登录 |

**账号注销流程**:
1. 首次请求: 账号进入 `pending_deletion` 状态，开始 15 天冷静期
2. 冷静期内登录: 自动恢复为 `active` 状态
3. 二次确认: 执行不可逆脱敏删除

---

## 5. 前端模块详解

### 5.1 页面结构

| 页面路径 | 功能描述 | 平台 |
|----------|----------|------|
| `pages/activities/activities` | 首页 - 活动列表 | App |
| `pages/activity/create/create` | 创建活动 | App |
| `pages/activity/detail/detail` | 活动详情 | 全平台 |
| `pages/activity/participants/participants` | 报名/签到管理 | App |
| `pages/activity/share/share` | 分享活动 | App |
| `pages/activity/ticket/ticket` | 报名凭证 | 全平台 |
| `pages/auth/login` | 登录页面 | 全平台 |
| `pages/profile/profile` | 个人中心 | 全平台 |
| `pages/user/my-activities/my-activities` | 我的报名 | 全平台 |
| `pages/user/created-activities/created-activities` | 我创建的活动 | App |

### 5.2 状态管理 (store/index.uts)

**全局状态**:
```typescript
activitiesState = {
  activities: Activity[],    // 活动列表
  user: User | null,         // 当前用户
  isLoading: boolean,        // 加载状态
  error: string,             // 错误信息
  isOnline: boolean          // 在线状态
}
```

**核心方法**:
| 方法 | 描述 |
|------|------|
| `fetchActivities(page, append)` | 拉取活动列表 |
| `addActivity(activity)` | 创建活动 (乐观更新) |
| `updateActivity(activity)` | 更新活动 (乐观更新) |
| `deleteActivity(id)` | 删除活动 (乐观删除) |
| `saveToStorage()` | 持久化到本地存储 |
| `loadFromStorage()` | 从本地存储恢复 |

### 5.3 网络请求封装 (utils/request.uts)

**请求拦截**:
- 自动注入 `Authorization` Header
- 自动注入 `Idempotency-Key` (非 GET 请求)
- 自动注入 `X-Client-Platform` / `X-App-Version`

**离线队列机制**:
- 离线时非 GET 请求自动入队
- 网络恢复后自动重放
- 支持临时 ID 到真实 ID 的映射

**错误处理**:
- 401: 自动跳转登录页
- 500: 显示服务器错误提示
- 网络错误: 入队或显示提示

---

## 6. 数据库设计

### 6.1 核心表结构

#### 用户表 (users)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 自增 ID |
| phone | String(20) | Unique, Index | 手机号 |
| openid | String(128) | Unique, Index | 微信 OpenID |
| username | String(64) | - | 昵称 |
| avatar_url | String(255) | - | 头像 URL |
| bio | Text | - | 个人简介 |
| is_certified | Boolean | Default(False) | 是否实名认证 |
| status | String(20) | Default('active') | active/pending_deletion/deleted |
| created_at | DateTime | - | 创建时间 |
| deletion_requested_at | DateTime | - | 注销冷静期开始时间 |

#### 活动表 (activities)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 自增 ID |
| user_id | Integer | FK(users.id) | 组织者 ID |
| name | String(128) | Not Null | 活动名称 |
| type | String(50) | - | 活动类型 |
| start_time | DateTime | Not Null | 开始时间 |
| end_time | DateTime | - | 结束时间 |
| location | String(255) | - | 地点 |
| description | Text | - | 详情描述 |
| capacity | Integer | Default(0) | 人数上限 (0=不限) |
| status | String(20) | Default('upcoming') | upcoming/ongoing/ended/cancelled |
| views_count | Integer | Default(0) | 浏览量 |
| host_phone | String(20) | - | 主办方电话 |
| host_wechat | String(64) | - | 主办方微信 |
| show_phone | Boolean | Default(False) | 是否公开电话 |
| show_wechat | Boolean | Default(False) | 是否公开微信 |
| created_at | DateTime | - | 创建时间 |
| updated_at | DateTime | - | 更新时间 |

#### 报名表 (registrations)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 自增 ID |
| activity_id | Integer | FK(activities.id) | 活动 ID |
| user_id | Integer | FK(users.id) | 用户 ID (可空) |
| name | String(64) | Not Null | 报名人姓名 |
| phone | String(20) | Not Null | 报名人电话 |
| created_at | DateTime | - | 报名时间 |

#### 签到记录表 (checkin_records)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 自增 ID |
| registration_id | Integer | FK, Unique | 报名记录 ID |
| activity_id | Integer | FK | 活动 ID (冗余) |
| checkin_time | DateTime | - | 签到时间 |
| device_info | String(255) | - | 设备指纹 |

### 6.2 实体关系

```
┌─────────┐       ┌───────────┐       ┌──────────────┐
│  User   │───1:N─│  Activity │───1:N─│ Registration │
└─────────┘       └───────────┘       └──────┬───────┘
                                              │
                                              │ 1:1
                                              ▼
                                       ┌──────────────┐
                                       │CheckinRecord │
                                       └──────────────┘
```

### 6.3 辅助表

| 表名 | 用途 |
|------|------|
| reports | 举报记录 |
| idempotency_keys | 幂等键记录 (防重复提交) |
| orgs | 组织/租户 |
| org_members | 组织成员 |
| plans | 套餐定义 |
| entitlements | 权益定义 |
| subscriptions | 订阅记录 |
| billing_events | 计费事件流水 |
| support_sessions | 客服会话 |
| event_logs | 埋点事件 |
| metrics_daily | 日维度聚合指标 |

---

## 7. API 接口定义

### 7.1 通用规范

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>        # 需登录的接口
Idempotency-Key: <uuid>              # POST/PUT/DELETE 接口
X-Client-Platform: ios|android|mp_weixin|h5
X-App-Version: 1.0.0
```

**响应格式**:
```json
// 成功响应
{
  "id": 1,
  "name": "活动名称",
  ...
}

// 错误响应
{
  "code": "ERROR_CODE",
  "message": "用户可读的错误描述",
  "request_id": "req_xxx"
}
```

### 7.2 错误码规范

| 错误码 | HTTP 状态 | 含义 |
|--------|-----------|------|
| REQ_INVALID | 400 | 请求参数错误 |
| AUTH_UNAUTHORIZED | 401 | 未登录或 Token 无效 |
| AUTH_FORBIDDEN | 403 | 无权限访问 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| RATE_LIMITED | 429 | 请求频率过高 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

---

## 8. 用户交互流程

### 8.1 活动创建流程

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 点击创建 │───▶│ 填写表单 │───▶│ 提交创建 │───▶│ 创建成功 │
└─────────┘    └────┬────┘    └────┬────┘    └─────────┘
                    │              │
                    ▼              ▼
              ┌───────────┐  ┌───────────────┐
              │ 表单校验  │  │ 内容安全校验  │
              │ - 名称必填│  │ (微信 msgSec) │
              │ - 时间必填│  └───────────────┘
              └───────────┘
```

### 8.2 报名签到流程

```
┌──────────────────────────────────────────────────────────────┐
│                        参与者视角                             │
├──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│ 浏览活动  │───▶│ 填写报名  │───▶│ 获取凭证  │───▶│ 扫码签到  │  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                        组织者视角                             │
├──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│ 查看名单  │───▶│ 扫码核销  │───▶│ 确认签到  │───▶│ 导出数据  │  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 8.3 账号注销流程

```
┌─────────┐    ┌───────────────┐    ┌─────────────┐
│ 发起注销 │───▶│ pending_deletion│───▶│ 15天冷静期  │
└─────────┘    └───────────────┘    └──────┬──────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
            ┌─────────────┐                             ┌─────────────┐
            │ 登录恢复账号 │                             │ 二次确认注销 │
            │ status=active│                             │ 数据脱敏删除 │
            └─────────────┘                             └─────────────┘
```

---

## 9. 数据流向

### 9.1 活动创建数据流

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│ 前端表单   │────▶│ 乐观更新   │────▶│ API 请求   │────▶│ 后端处理   │
│ Activity   │     │ Store      │     │ request()  │     │ Flask      │
└────────────┘     └────────────┘     └────────────┘     └─────┬──────┘
                                                                │
                        ┌───────────────────────────────────────┤
                        ▼                                       ▼
                 ┌────────────┐                         ┌────────────┐
                 │ 内容安全   │                         │ 数据库写入 │
                 │ msgSecCheck│                         │ SQLite/PG  │
                 └────────────┘                         └────────────┘
```

### 9.2 离线数据同步流

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│ 离线操作   │────▶│ 入队存储   │────▶│ 网络恢复   │
│ (创建/更新) │     │ offline_   │     │ onNetwork  │
└────────────┘     │ queue      │     │ Change     │
                   └────────────┘     └──────┬─────┘
                                             │
                   ┌─────────────────────────┘
                   ▼
            ┌────────────┐     ┌────────────┐     ┌────────────┐
            │ 队列重放   │────▶│ ID 映射更新│────▶│ Store 同步 │
            │ processQueue│    │ tempId→realId│   │ 刷新列表   │
            └────────────┘     └────────────┘     └────────────┘
```

---

## 10. 离线机制

### 10.1 离线队列实现

**触发条件**:
- 设备离线时执行非 GET 请求
- 网络请求失败 (uni.request fail)

**队列数据结构**:
```typescript
QueueItem = {
  id: string,           // 队列项唯一标识
  url: string,          // API 路径
  method: string,       // HTTP 方法
  data: any,            // 请求体
  header: object,       // 请求头
  tempId: number,       // 临时 ID (用于映射)
  timestamp: number     // 入队时间
}
```

**存储位置**: `uni.setStorageSync('offline_queue', queue)`

### 10.2 临时 ID 映射

**问题**: 离线创建活动时，后端尚未返回真实 ID

**解决方案**:
1. 离线创建时分配负数临时 ID (`-Date.now()`)
2. 同步成功后建立映射关系
3. 前端通过映射表查找真实 ID

**映射存储**: `uni.setStorageSync('activity_id_mapping', mapping)`

### 10.3 乐观更新策略

| 操作 | 乐观行为 | 失败回滚 |
|------|----------|----------|
| 创建活动 | 立即添加到 Store | 从 Store 移除 |
| 更新活动 | 立即更新 Store | 恢复旧值 |
| 删除活动 | 立即从 Store 移除 | 重新插入原位置 |

---

## 11. 安全机制

### 11.1 认证安全

| 机制 | 描述 |
|------|------|
| JWT Token | 7 天有效期，自动续期 |
| 验证码 | 60 秒发送频率限制，5 分钟有效期 |
| Redis 存储 | 生产环境验证码存储，支持 TTL |

### 11.2 接口安全

| 机制 | 描述 |
|------|------|
| 幂等控制 | POST/PUT/DELETE 接口需携带 Idempotency-Key |
| 请求限流 | 默认 200次/天，50次/小时 |
| HTTPS | 生产环境强制 HTTPS (Talisman) |
| CORS | 跨域请求支持 |

### 11.3 数据安全

| 机制 | 描述 |
|------|------|
| 手机号脱敏 | 非组织者查看报名时显示 `138****5678` |
| 微信号脱敏 | 非组织者查看时显示 `wx****id` |
| 内容安全 | 微信 msgSecCheck 接口校验违规内容 |
| 级联删除 | 活动删除时自动删除关联的报名/签到记录 |

### 11.4 合规机制

| 要求 | 实现 |
|------|------|
| iOS 5.1.1(v) | 15 天账号注销冷静期 |
| 微信运营规范 | 内容安全校验、举报机制 |
| GDPR | 账号注销时数据脱敏删除 |

---

## 12. 部署说明

### 12.1 环境变量

```bash
# 数据库
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis
REDIS_URL=redis://host:6379/0

# 微信
WECHAT_APP_ID=wx...
WECHAT_APP_SECRET=...
WECHAT_API_TOKEN=...

# 短信服务
SMS_ACCESS_KEY_ID=...
SMS_ACCESS_KEY_SECRET=...
SMS_SIGN_NAME=...
SMS_TEMPLATE_CODE=...

# 安全
SECRET_KEY=your-secret-key
FORCE_HTTPS=true

# Apple 登录
APPLE_BUNDLE_ID=com.yourcompany.activityassistant
```

### 12.2 启动命令

```bash
# 开发环境
python run.py

# 生产环境 (阿里云函数计算)
# 使用 fc_handler.py 作为入口

# 初始化测试数据
python seed.py
```

### 12.3 前端构建

```bash
# 开发模式 (使用 Mock 数据)
# 修改 utils/config.uts 中 USE_MOCK = true

# 生产构建
# HBuilderX -> 发行 -> 原生App/小程序
```

---

## 附录

### A. 前端类型定义

**Activity 类型**:
```typescript
interface Activity {
  id: number;
  name: string;
  type: string;
  date: string;           // YYYY-MM-DD
  time: string;           // HH:mm
  endTime: string | null; // HH:mm
  location: string;
  description: string;
  capacity: number;
  participants: number;   // 报名人数
  checkins: number;       // 签到人数
  views: number;          // 浏览量
  status: string;         // upcoming/ongoing/ended/cancelled
  organizer_id: number;
  host_phone: string | null;
  host_wechat: string | null;
  show_phone: boolean;
  show_wechat: boolean;
  checkinRecords: CheckinRecord[];
  registrations: Registration[];
  createdAt: string;
  syncStatus?: 'synced' | 'pending' | 'failed';
}
```

### B. 后端模型方法

**Activity.calculate_status()**:
- 根据当前时间动态计算活动状态
- 优先级: cancelled > upcoming > ongoing > ended

**User.to_dict(mask)**:
- 转换为 JSON 可序列化字典
- mask=True 时手机号脱敏

### C. 埋点事件

| 事件名 | 触发时机 |
|--------|----------|
| app_launch | 应用启动 |
| network_change | 网络状态变化 |
| activity_create_success | 活动创建成功 |
| activity_create_offline_queued | 活动创建离线入队 |
| activity_update_success | 活动更新成功 |
| activity_delete_success | 活动删除成功 |
| registration_cancelled | 取消报名 |
| user_account_deleted_final | 账号最终注销 |
| content_reported | 内容举报 |
| global_error | 全局错误 |

---

## 13. 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 产品需求文档 | [01_Product/PRD.md](./01_Product/PRD.md) | 产品需求与功能规划 |
| 功能规格说明书 | [01_Product/Feature_Specification.md](./01_Product/Feature_Specification.md) | 详细功能规格与策略 |
| API 接口文档 | [02_Technical/API_Reference.md](./02_Technical/API_Reference.md) | API 接口定义 |
| 数据库设计 | [02_Technical/Database_Design.md](./02_Technical/Database_Design.md) | 数据库表结构 |
| 埋点需求文档 | [02_Technical/Analytics_Requirements.md](./02_Technical/Analytics_Requirements.md) | 埋点事件定义 |
| 架构分析 | [02_Technical/Architecture_Analysis.md](./02_Technical/Architecture_Analysis.md) | 技术架构分析 |
| 用户手册 | [05_User_Support/User_Manual.md](./05_User_Support/User_Manual.md) | 用户使用指南 |
| 隐私政策 | [07_Legal/Privacy_Policy.md](./07_Legal/Privacy_Policy.md) | 隐私政策 |
| 用户协议 | [07_Legal/User_Agreement.md](./07_Legal/User_Agreement.md) | 用户服务协议 |

---

## 附录

### A. 版本信息

- **当前版本**：v1.0.0
- **开发技术**：uni-app x (UTS) + Python Flask
- **运行平台**：iOS / Android / 微信小程序
- **文档更新日期**：2026-03-26
