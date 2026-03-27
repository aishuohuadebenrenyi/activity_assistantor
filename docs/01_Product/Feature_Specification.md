# Zentro 产品功能说明书

> **Version**: v1.0.0 | **Last Updated**: 2026-03-26

---

## 目录

1. [产品概述](#1-产品概述)
2. [多端策略](#2-多端策略)
3. [用户管理功能](#3-用户管理功能)
4. [活动管理功能](#4-活动管理功能)
5. [报名与签到功能](#5-报名与签到功能)
6. [数据统计功能](#6-数据统计功能)
7. [商业化功能](#7-商业化功能)
8. [客服支持功能](#8-客服支持功能)
9. [系统配置与安全策略](#9-系统配置与安全策略)
10. [离线机制](#10-离线机制)
11. [埋点与数据分析](#11-埋点与数据分析)

---

## 1. 产品概述

### 1.1 产品定位

**Zentro** 是一款面向活动组织者的移动端活动管理应用，采用 **uni-app x** 跨平台框架开发，支持 iOS、Android 和微信小程序三端运行。

### 1.2 目标用户

| 用户类型 | 描述 | 核心需求 |
|---------|------|---------|
| 社区运营 | 社群活动组织者 | 快速发布活动、管理报名名单 |
| 企业行政/HR | 企业内部活动组织者 | 员工活动管理、签到统计 |
| 培训负责人 | 培训机构/企业培训师 | 培训签到、数据导出 |
| 社群组织者 | 兴趣社群/俱乐部 | 活动发布、成员管理 |

### 1.3 核心价值

| 价值点 | 描述 |
|--------|------|
| 快速发起 | 简化活动创建流程，3分钟完成发布 |
| 过程可控 | 实时查看报名/签到状态，支持现场核销 |
| 数据可见 | 浏览量、报名率、签到率等关键指标可视化 |

---

## 2. 多端策略

### 2.1 平台角色分工

| 平台 | 核心角色 | 主要功能 | TabBar 配置 |
|------|---------|---------|-------------|
| iOS/Android App | 主办方/管理员 | 创建活动、管理报名、扫码核销、导出数据 | 首页 \| 创建 \| 我的 |
| 微信小程序 | 参与者/用户 | 浏览活动、在线报名、查看电子票、扫码签到 | 我的报名 \| 个人中心 |

### 2.2 平台能力差异

| 能力维度 | App 端 | 小程序端 |
|---------|--------|----------|
| 创建活动 | ✅ 完整支持 | ❌ 不支持 |
| 编辑活动 | ✅ 完整支持 | ❌ 不支持 |
| 删除活动 | ✅ 完整支持 | ❌ 不支持 |
| 扫码核销 | ✅ 完整支持 | ❌ 不支持 |
| 浏览活动 | ✅ | ✅ |
| 报名活动 | ✅ | ✅ |
| 查看凭证 | ✅ | ✅ |
| 离线支持 | 强（支持管理操作队列） | 弱（仅支持基础缓存） |

### 2.3 条件编译配置

```
// 小程序专属页面
pages/user/my-activities/my-activities  // 小程序首页
pages/webview/webview                   // 协议展示

// App 专属页面
pages/activity/create/create            // 创建活动
pages/user/created-activities/created-activities  // 我创建的活动
pages/profile/edit/edit                 // 编辑资料
```

---

## 3. 用户管理功能

### 3.1 登录注册

#### 3.1.1 登录方式

| 登录方式 | 接口 | 适用平台 | 说明 |
|---------|------|---------|------|
| 手机号验证码登录 | `POST /api/auth/login` | 全平台 | 自动注册，首次登录创建账号 |
| 微信登录 | `POST /api/auth/login/wechat` | 小程序/App | code 换取 openid |
| Apple 登录 | `POST /api/auth/login/apple` | iOS | App Store 强制要求 |

#### 3.1.2 验证码策略

| 策略项 | 规则 |
|--------|------|
| 发送频率 | 同一手机号 60 秒内仅允许发送一次 |
| 有效期 | 5 分钟 |
| 存储方式 | 生产环境 Redis，开发环境内存字典 |
| 兜底验证码 | 开发/测试环境支持 `123456` |

#### 3.1.3 手机号格式校验

```
正则: ^1[3-9]\d{9}$
说明: 中国大陆手机号格式
```

#### 3.1.4 JWT Token 策略

| 配置项 | 值 |
|--------|-----|
| 有效期 | 7 天 |
| 算法 | HS256 |
| 载荷 | user_id, exp |

### 3.2 个人资料管理

#### 3.2.1 资料字段

| 字段 | 类型 | 可修改 | 说明 |
|------|------|--------|------|
| phone | String(20) | 否 | 手机号（登录后自动绑定） |
| openid | String(128) | 否 | 微信 OpenID |
| username | String(64) | ✅ | 昵称，默认"用户" |
| avatar_url | String(255) | ✅ | 头像 URL |
| bio | Text | ✅ | 个人简介 |
| is_certified | Boolean | 否 | 是否实名认证 |

#### 3.2.2 接口定义

| 接口 | 方法 | 描述 |
|------|------|------|
| `GET /api/user/profile` | GET | 获取个人资料 |
| `PUT /api/user/profile` | PUT | 更新个人资料 |

### 3.3 账号注销

#### 3.3.1 注销流程

```
┌─────────────┐     ┌───────────────────┐     ┌─────────────┐
│  发起注销    │────▶│ pending_deletion  │────▶│  15天冷静期  │
│  DELETE请求 │     │    状态变更        │     │             │
└─────────────┘     └───────────────────┘     └──────┬──────┘
                                                      │
                       ┌──────────────────────────────┴──────────────────────┐
                       ▼                                                     ▼
               ┌─────────────┐                                       ┌─────────────┐
               │ 登录恢复账号 │                                       │ 二次确认注销 │
               │status=active│                                       │ 数据脱敏删除 │
               └─────────────┘                                       └─────────────┘
```

#### 3.3.2 注销规则

| 规则项 | 说明 |
|--------|------|
| 冷静期 | 15 天（符合 iOS App Store 指南 5.1.1(v)） |
| 恢复方式 | 冷静期内登录自动恢复 |
| 二次确认 | 冷静期内再次调用注销接口执行最终删除 |
| 数据处理 | 不可逆脱敏，保留审计记录 |

#### 3.3.3 脱敏删除策略

| 数据类型 | 处理方式 |
|---------|---------|
| 用户记录 | phone 替换为 `DELETED_{id}_{timestamp}`，openid 置空 |
| 发布的活动 | 级联删除（含报名、签到记录） |
| 报名记录 | 通过旧手机号关联的报名记录删除 |

### 3.4 举报功能

#### 3.4.1 举报类型

| 类型 | 说明 |
|------|------|
| activity | 活动举报 |
| user | 用户举报（预留） |

#### 3.4.2 举报流程

| 接口 | 方法 | 描述 |
|------|------|------|
| `POST /api/user/report` | POST | 提交举报 |
| `POST /api/activities/<id>/report` | POST | 举报活动 |
| `GET /api/user/reports` | GET | 获取我的举报记录 |

#### 3.4.3 举报规则

| 规则项 | 说明 |
|--------|------|
| 防重复 | 同一用户对同一目标仅能举报一次 |
| 状态流转 | pending → processed / rejected |
| 响应时效 | 承诺 24 小时内核实处理 |

---

## 4. 活动管理功能

### 4.1 活动创建

#### 4.1.1 创建接口

```
POST /api/activities
需要登录: 是
幂等控制: Idempotency-Key
```

#### 4.1.2 活动字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String(128) | ✅ | 活动名称 |
| type | String(50) | 否 | 活动类型，默认"其他" |
| date | Date | ✅ | 活动日期 |
| time | Time | ✅ | 开始时间 |
| end_date | Date | 否 | 结束日期 |
| end_time | Time | 否 | 结束时间 |
| location | String(255) | 否 | 活动地点 |
| description | Text | 否 | 活动描述 |
| capacity | Integer | 否 | 人数上限，0 表示不限 |
| host_phone | String(20) | 否 | 主办方电话 |
| host_wechat | String(64) | 否 | 主办方微信 |
| show_phone | Boolean | 否 | 是否公开电话，默认 false |
| show_wechat | Boolean | 否 | 是否公开微信，默认 false |

#### 4.1.3 内容安全校验

| 校验字段 | 校验方式 |
|---------|---------|
| name | 微信 msgSecCheck |
| description | 微信 msgSecCheck |
| location | 微信 msgSecCheck |
| host_wechat | 微信 msgSecCheck |

### 4.2 活动状态

#### 4.2.1 状态定义

| 状态 | 英文 | 判断规则 |
|------|------|---------|
| 即将开始 | upcoming | start_time > 当前时间 |
| 进行中 | ongoing | start_time ≤ 当前时间 < end_time |
| 已结束 | ended | 当前时间 ≥ end_time |
| 已取消 | cancelled | 手动设置（优先级最高） |

#### 4.2.2 状态计算逻辑

```python
def calculate_status(self):
    if self.status == 'cancelled':
        return 'cancelled'
    
    now = datetime.utcnow()
    
    if self.start_time > now:
        return 'upcoming'
    
    effective_end_time = self.end_time or self.start_time + timedelta(hours=24)
    if now < effective_end_time:
        return 'ongoing'
    
    return 'ended'
```

### 4.3 活动列表

#### 4.3.1 列表接口

```
GET /api/activities
需要登录: 否
支持参数: status, search, page, page_size
```

#### 4.3.2 筛选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| status | String | all | 状态筛选：all/ongoing/upcoming/ended |
| search | String | - | 按名称或地点模糊搜索 |
| page | Integer | 1 | 页码 |
| page_size | Integer | 20 | 每页数量，最大 100 |

#### 4.3.3 返回结构

```json
{
  "activities": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

### 4.4 活动详情

#### 4.4.1 详情接口

```
GET /api/activities/<id>
需要登录: 否
```

#### 4.4.2 浏览量统计

| 规则 | 说明 |
|------|------|
| 触发时机 | 每次访问详情页 |
| 增量 | +1 |
| 存储 | views_count 字段 |

#### 4.4.3 敏感信息保护

| 场景 | 手机号显示 | 微信号显示 |
|------|-----------|-----------|
| 组织者查看 | 明文 | 明文 |
| 已报名用户 | 脱敏 | 脱敏 |
| 未报名用户 | 不显示 | 不显示 |

### 4.5 活动编辑

#### 4.5.1 编辑接口

```
PUT /api/activities/<id>
需要登录: 是
权限: 仅组织者可编辑
幂等控制: Idempotency-Key
```

#### 4.5.2 可编辑字段

与创建字段相同，支持部分更新。

### 4.6 活动删除

#### 4.6.1 删除接口

```
DELETE /api/activities/<id>
需要登录: 是
权限: 仅组织者可删除
幂等控制: Idempotency-Key
```

#### 4.6.2 级联删除

| 关联数据 | 删除策略 |
|---------|---------|
| registrations | 级联删除 |
| checkin_records | 级联删除 |

### 4.7 活动分享

#### 4.7.1 分享接口

```
GET /api/activities/<id>/share
需要登录: 否
```

#### 4.7.2 分享内容

| 内容 | 说明 |
|------|------|
| url_link | 微信 URL Link（30天有效） |
| qrcode_data | 小程序码数据 |
| activity_name | 活动名称 |
| activity_info | 活动详情 |

---

## 5. 报名与签到功能

### 5.1 活动报名

#### 5.1.1 报名接口

```
POST /api/activities/<id>/register
需要登录: 是
幂等控制: Idempotency-Key
```

#### 5.1.2 报名字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String(64) | ✅ | 报名人姓名 |
| phone | String(20) | ✅ | 报名人手机号 |

#### 5.1.3 报名规则

| 规则项 | 说明 |
|--------|------|
| 重复报名检测 | 通过 user_id 或 phone 判断 |
| 活动状态校验 | 已开始/已结束的活动不可报名 |
| 容量校验 | 名额已满不可报名 |
| 自动关联 | 自动关联当前登录用户的 user_id |

### 5.2 取消报名

#### 5.2.1 取消接口

```
DELETE /api/activities/<id>/register
需要登录: 是
```

#### 5.2.2 取消规则

| 规则项 | 说明 |
|--------|------|
| 匹配方式 | 优先 user_id，其次 phone |
| 已签到限制 | 已签到的报名不可取消 |
| 时间限制 | 活动已开始后不可取消 |

### 5.3 报名凭证

#### 5.3.1 凭证接口

```
GET /api/activities/<id>/my-ticket
需要登录: 是
```

#### 5.3.2 凭证内容

| 内容 | 说明 |
|------|------|
| registration | 报名信息 |
| ticket_code | Base64 签到码 |
| qr_code_image | Base64 二维码图片 |
| activity | 活动信息（含主办方联系方式） |

#### 5.3.3 签到码格式

```
CHECKIN:<activity_id>:<registration_id>:<timestamp>:<signature>
```

### 5.4 签到核销

#### 5.4.1 签到接口

```
POST /api/activities/<id>/checkin
需要登录: 是
权限: 仅组织者可核销
幂等控制: Idempotency-Key
```

#### 5.4.2 签到方式

| 方式 | 参数 | 说明 |
|------|------|------|
| 扫码签到 | qr_data | Base64 签到码 |
| 手动签到 | registration_id | 直接传报名记录 ID |

#### 5.4.3 签到码验证

| 验证项 | 说明 |
|--------|------|
| 格式验证 | 检查 CHECKIN 前缀和字段数量 |
| 活动匹配 | 验证 activity_id 是否匹配 |
| 签名验证 | HMAC-SHA256 签名校验 |
| 过期验证 | 签到码有效期 7 天 |

### 5.5 取消签到

#### 5.5.1 取消接口

```
DELETE /api/activities/<id>/checkin/<registration_id>
需要登录: 是
权限: 仅组织者可操作
```

### 5.6 报名名单

#### 5.6.1 名单接口

```
GET /api/activities/<id>/participants
需要登录: 是
权限: 仅组织者可查看
```

#### 5.6.2 返回字段

| 字段 | 说明 |
|------|------|
| id | 报名记录 ID |
| name | 姓名 |
| phone | 手机号（明文） |
| created_at | 报名时间 |
| checked_in | 是否已签到 |
| checkin_time | 签到时间 |

### 5.7 数据导出

#### 5.7.1 导出接口

```
POST /api/activities/<id>/export
需要登录: 是
权限: 仅组织者可导出
幂等控制: Idempotency-Key
```

#### 5.7.2 导出参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | String | ✅ | 接收导出的邮箱 |

#### 5.7.3 导出格式

| 字段 | 说明 |
|------|------|
| ID | 报名记录 ID |
| 姓名 | 报名人姓名 |
| 电话 | 报名人手机号 |
| 报名时间 | ISO 格式时间 |
| 是否签到 | 是/否 |
| 签到时间 | ISO 格式时间 |

---

## 6. 数据统计功能

### 6.1 活动统计看板

#### 6.1.1 核心指标

| 指标 | 定义 | 计算方式 |
|------|------|---------|
| 浏览量 | 活动详情页打开次数 | views_count |
| 报名人数 | 成功报名人数 | COUNT(registrations) |
| 签到人数 | 实际签到人数 | COUNT(checkin_records) |
| 签到率 | 实际签到/报名人数 | checkins / participants |

### 6.2 埋点事件上报

#### 6.2.1 上报接口

```
POST /api/analytics/events
需要登录: 否
批量限制: 单次最多 100 个事件
```

#### 6.2.2 事件结构

```json
{
  "events": [
    {
      "event_id": "uuid",
      "event_name": "activity_create_success",
      "timestamp": 1711459200000,
      "user_id": 1,
      "device_id": "device_xxx",
      "session_id": "session_xxx",
      "platform": "ios",
      "app_version": "1.0.0",
      "properties": {
        "id": 123,
        "name": "活动名称"
      }
    }
  ],
  "device_info": {
    "model": "iPhone 15",
    "os_version": "17.0"
  }
}
```

### 6.3 统计查询

#### 6.3.1 事件查询接口

```
POST /api/analytics/events/query
```

#### 6.3.2 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| event_names | Array | 事件名称列表 |
| start_time | Timestamp/ISO | 开始时间 |
| end_time | Timestamp/ISO | 结束时间 |
| user_id | Integer | 用户 ID |
| platform | String | 平台标识 |
| limit | Integer | 返回数量限制 |
| offset | Integer | 偏移量 |

### 6.4 日统计

#### 6.4.1 日统计接口

```
GET /api/analytics/stats/daily?date=2026-03-26
```

#### 6.4.2 返回指标

| 指标 | 说明 |
|------|------|
| dau | 日活用户数 |
| device_count | 活跃设备数 |
| event_counts | 各事件发生次数 |
| platform_distribution | 平台分布 |

### 6.5 漏斗分析

#### 6.5.1 漏斗接口

```
POST /api/analytics/stats/funnel
```

#### 6.5.2 漏斗参数

```json
{
  "steps": [
    {"event_name": "app_launch"},
    {"event_name": "activity_create_start"},
    {"event_name": "activity_create_success"}
  ],
  "start_time": "2026-03-01T00:00:00Z",
  "end_time": "2026-03-31T23:59:59Z"
}
```

---

## 7. 商业化功能

### 7.1 组织管理

#### 7.1.1 组织概念

| 概念 | 说明 |
|------|------|
| 组织(Org) | 计费和团队协作的基本单位 |
| 默认组织 | 每个用户自动创建一个默认组织 |
| 组织成员 | 支持添加成员（预留功能） |

#### 7.1.2 组织接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `GET /api/org/me` | GET | 获取我的组织 |
| `PUT /api/org/me` | PUT | 更新组织名称 |
| `GET /api/org/me/members` | GET | 获取组织成员 |

### 7.2 套餐体系

#### 7.2.1 套餐定义

| 字段 | 类型 | 说明 |
|------|------|------|
| code | String | 套餐唯一标识 |
| name | String | 套餐名称 |
| period | String | 计费周期：month/year |
| status | String | 状态：active/inactive |
| sort | Integer | 展示排序 |

#### 7.2.2 套餐接口

```
GET /api/billing/plans
```

### 7.3 权益体系

#### 7.3.1 权益定义

| 权益键 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| export.enabled | bool | true | 是否支持导出 |
| activity.max_count | int | 9999 | 活动数量上限 |
| team.enabled | bool | false | 是否支持团队协作 |

#### 7.3.2 权益接口

```
GET /api/billing/me/entitlements
需要登录: 是
```

### 7.4 订阅管理

#### 7.4.1 订阅状态

| 状态 | 说明 |
|------|------|
| trialing | 试用中 |
| active | 有效订阅 |
| canceled | 已取消 |

#### 7.4.2 订阅接口

```
GET /api/billing/me/subscription
需要登录: 是
```

### 7.5 手动授权

#### 7.5.1 授权接口

```
POST /api/billing/admin/manual-grant
需要登录: 是
用途: 演示/内测/灰度
```

#### 7.5.2 授权参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| plan_code | String | free | 套餐代码 |
| days | Integer | 30 | 有效天数 |

---

## 8. 客服支持功能

### 8.1 客服入口

#### 8.1.1 入口配置接口

```
GET /api/support/entry?scene=feedback&platform=ios
需要登录: 是
```

#### 8.1.2 返回内容

| 内容 | 说明 |
|------|------|
| customer_service_url | 客服链接（配置项） |
| context_token | 上下文 token |
| context | 结构化上下文信息 |

#### 8.1.3 场景标识

| 场景 | 标识 |
|------|------|
| 意见反馈 | feedback |
| 个人中心 | profile |
| 活动详情 | activity_detail |

### 8.2 会话记录

#### 8.2.1 会话记录接口

```
POST /api/support/session
需要登录: 是
幂等控制: Idempotency-Key
```

#### 8.2.2 会话字段

| 字段 | 类型 | 说明 |
|------|------|------|
| status | String | opened/closed |
| platform | String | 平台标识 |
| entry_point | String | 入口场景 |
| external_session_id | String | 外部会话 ID |
| category | String | 问题分类 |
| satisfaction | Integer | 满意度评分 |
| first_response_ms | Integer | 首次响应时间 |
| context_snapshot | JSON | 上下文快照 |

---

## 9. 系统配置与安全策略

### 9.1 认证安全

| 机制 | 配置 | 说明 |
|------|------|------|
| JWT Token | 7 天有效期 | 自动续期 |
| 验证码 | 60 秒频率限制 | 5 分钟有效期 |
| Redis 存储 | 生产环境 | 支持 TTL 和多进程共享 |

### 9.2 接口安全

| 机制 | 说明 |
|------|------|
| 幂等控制 | POST/PUT/DELETE 接口需携带 Idempotency-Key |
| 请求限流 | 默认 200 次/天，50 次/小时 |
| HTTPS | 生产环境强制 HTTPS (Talisman) |
| CORS | 跨域请求支持 |

### 9.3 数据安全

| 机制 | 说明 |
|------|------|
| 手机号脱敏 | 非组织者查看显示 `138****5678` |
| 微信号脱敏 | 非组织者查看显示 `wx****id` |
| 内容安全 | 微信 msgSecCheck 接口校验 |
| 级联删除 | 活动删除时自动删除关联数据 |

### 9.4 环境变量配置

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
QR_SECRET_KEY=qr-signing-key

# Apple 登录
APPLE_BUNDLE_ID=com.yourcompany.activityassistant

# 客服
CUSTOMER_SERVICE_URL=https://...
```

---

## 10. 离线机制

### 10.1 离线队列

#### 10.1.1 触发条件

| 条件 | 说明 |
|------|------|
| 设备离线 | 执行非 GET 请求时自动入队 |
| 网络请求失败 | uni.request fail 时入队 |

#### 10.1.2 队列数据结构

```typescript
interface QueueItem {
  id: string;           // 队列项唯一标识
  url: string;          // API 路径
  method: string;       // HTTP 方法
  data: any;            // 请求体
  header: object;       // 请求头
  tempId: number;       // 临时 ID（用于映射）
  timestamp: number;    // 入队时间
  retryCount: number;   // 重试次数
  maxRetry: number;     // 最大重试次数
}
```

#### 10.1.3 队列限制

| 限制项 | 值 |
|--------|-----|
| 最大队列长度 | 100 条 |
| 队列有效期 | 7 天 |
| 默认最大重试 | 3 次 |

### 10.2 临时 ID 映射

#### 10.2.1 映射机制

| 步骤 | 说明 |
|------|------|
| 1. 离线创建 | 分配负数临时 ID (`-Date.now()`) |
| 2. 同步成功 | 建立临时 ID 与真实 ID 映射 |
| 3. 前端查询 | 通过映射表查找真实 ID |

#### 10.2.2 映射存储

```
uni.setStorageSync('activity_id_mapping', mapping)
```

### 10.3 乐观更新

| 操作 | 乐观行为 | 失败回滚 |
|------|----------|----------|
| 创建活动 | 立即添加到 Store | 从 Store 移除 |
| 更新活动 | 立即更新 Store | 恢复旧值 |
| 删除活动 | 立即从 Store 移除 | 重新插入原位置 |

---

## 11. 埋点与数据分析

### 11.1 埋点事件分类

#### 11.1.1 用户生命周期事件

| 事件名 | 触发时机 |
|--------|----------|
| app_launch | 应用启动 |
| app_background | 应用进入后台 |
| user_login | 用户登录成功 |
| user_logout | 用户登出 |
| user_account_deletion_pending | 账号注销进入冷静期 |
| user_account_deleted_final | 账号最终注销 |

#### 11.1.2 活动生命周期事件

| 事件名 | 触发时机 |
|--------|----------|
| activity_create_start | 开始创建活动 |
| activity_create_success | 活动创建成功 |
| activity_create_offline_queued | 活动创建离线入队 |
| activity_update_success | 活动更新成功 |
| activity_delete_success | 活动删除成功 |
| activity_view | 查看活动详情 |

#### 11.1.3 报名签到事件

| 事件名 | 触发时机 |
|--------|----------|
| registration_start | 开始报名 |
| registration_success | 报名成功 |
| registration_cancelled | 取消报名 |
| checkin_scan | 扫描签到码 |
| checkin_success | 签到成功 |
| checkin_cancelled | 取消签到 |

### 11.2 友盟+ 集成

#### 11.2.1 配置项

```json
{
  "app-plus": {
    "distribute": {
      "sdkConfigs": {
        "statics": {
          "umeng": {
            "appkey_ios": "...",
            "appkey_android": "...",
            "channel_ios": "AppStore",
            "channel_android": "GooglePlay"
          }
        }
      }
    }
  }
}
```

#### 11.2.2 初始化

```typescript
// App.uvue
import { initUmeng, trackEvent } from '@/utils/analytics/umeng.uts'

onLaunch() {
  initUmeng()
  trackEvent('app_launch', { platform: 'ios' })
}
```

### 11.3 数据指标

#### 11.3.1 核心指标

| 指标 | 定义 | 商业价值 |
|------|------|----------|
| DAU | 日活跃用户数 | 衡量产品活跃度 |
| MAU | 月活跃用户数 | 衡量产品规模 |
| 留存率 | 次日/7日/30日留存 | 衡量用户粘性 |
| 转化漏斗 | 浏览→报名→签到 | 识别流失环节 |

#### 11.3.2 业务指标

| 指标 | 定义 | 计算方式 |
|------|------|---------|
| 活动创建率 | 创建活动的用户占比 | 创建用户数 / DAU |
| 平均报名人数 | 每个活动平均报名人数 | 总报名数 / 活动数 |
| 签到率 | 实际签到/报名人数 | 签到数 / 报名数 |

---

## 附录

### A. API 接口汇总

| 模块 | 接口数量 | 主要功能 |
|------|---------|---------|
| 认证模块 | 4 | 登录/注册/验证码 |
| 活动模块 | 9 | CRUD/分享/签到/举报 |
| 参与者模块 | 5 | 报名/取消/导出/名单 |
| 用户模块 | 6 | 资料/注销/举报/报名列表 |
| 组织模块 | 3 | 组织管理 |
| 计费模块 | 4 | 套餐/权益/订阅 |
| 分析模块 | 6 | 事件上报/统计/健康检查 |
| 客服模块 | 2 | 入口/会话 |

### B. 数据库表汇总

| 表名 | 用途 | 主要字段 |
|------|------|---------|
| users | 用户信息 | id, phone, openid, username |
| activities | 活动信息 | id, user_id, name, start_time, status |
| registrations | 报名记录 | id, activity_id, user_id, name, phone |
| checkin_records | 签到记录 | id, registration_id, activity_id |
| reports | 举报记录 | id, activity_id, user_id, reason |
| orgs | 组织信息 | id, owner_user_id, name |
| plans | 套餐定义 | id, code, name, period |
| subscriptions | 订阅记录 | id, org_id, plan_id, status |
| event_logs | 埋点事件 | id, event_name, user_id, platform |

### C. 版本信息

- **当前版本**：v1.0.0
- **开发技术**：uni-app x (UTS) + Python Flask
- **运行平台**：iOS / Android / 微信小程序
- **文档更新日期**：2026-03-26
