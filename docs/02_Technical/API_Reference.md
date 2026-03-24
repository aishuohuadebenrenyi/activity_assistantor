# API 接口文档

> **Version**: v1.0.0 | **Last Updated**: 2026-03-24

## 1. 概览

- **Base URL**: `https://your-domain.com/api` (生产环境)
- **认证方式**: Bearer Token
  - Header: `Authorization: Bearer <token>`
- **幂等控制**: 
  - Header: `Idempotency-Key: <unique_uuid>`
  - 适用接口：所有 `POST` / `PUT` / `DELETE` 接口

---

## 2. 认证接口

### 2.1 发送验证码
```
POST /auth/send-code
```
**Request:**
```json
{ "phone": "13800138000" }
```
**Response:**
```json
{ "message": "验证码已发送" }
```

### 2.2 手机号登录
```
POST /auth/login
```
**Request:**
```json
{ "phone": "13800138000", "code": "123456" }
```
**Response:**
```json
{ "token": "ey...", "user": { "id": 1, "phone": "138..." } }
```

### 2.3 微信登录
```
POST /auth/login/wechat
```
**Request:**
```json
{ "code": "wxcode...", "encrypted_data": "...", " "iv": "..." }
```
**Response:**
```json
{ "token": "ey...", "user": { "id": 1, " "openid": "..." } }
```

### 2.4 Apple 登录
```
POST /auth/login/apple
```
**Request:**
```json
{ "identity_token": "...", " "user": { "email": "..." } }
```
**Response:**
```json
{ "token": "ey...", "user": { "id": 1 } }
```

---

## 3. 活动接口

### 3.1 获取活动列表
```
GET /activities/?status=all&search=关键词
```
**Query Params:**
- `status`: all / ongoing / upcoming / ended
- `search`: 搜索关键词

**Response:** `[Activity]`

### 3.2 创建活动
```
POST /activities/
```
**Request:**
```json
{
  "name": "产品发布会",
  "type": "meeting",
  "date": "2023-10-01",
  "time": "14:00",
  "location": "北京",
  "description": "...",
  "capacity": 100
}
```
**Response:** `Activity`

### 3.3 获取活动详情
```
GET /activities/<id>
```
**Response:** `Activity`

### 3.4 更新活动
```
PUT /activities/<id>
```
**Request:** `{ "name": "新名称" }`
**Response:** `Activity`

### 3.5 删除活动
```
DELETE /activities/<id>
```
**Response:** `{ "message": "Activity deleted" }`

---

## 4. 报名与签到接口

### 4.1 报名活动
```
POST /activities/<id>/register
```
**Request:**
```json
{ "name": "张三", " "phone": "13900000000" }
```
**Response:** `Registration`

### 4.2 获取报名列表
```
GET /activities/<id>/participants
```
**Response:** `[Registration]`

### 4.3 签到
```
POST /activities/<id>/checkin
```
**Request:**
```json
{ "registration_id": 123,  "device_info": "iPhone 14" }
```
**Response:** `CheckinRecord`

### 4.4 取消签到
```
DELETE /activities/<id>/checkin/<record_id>
```
**Response:** `{ "message": "Checkin cancelled" }`

### 4.5 导出报名名单
```
POST /activities/<id>/export
```
**Request:**
```json
{ "email": "user@example.com" }
```
**Response:** `{ "message": "导出任务已提交" }`

---

## 5. 用户接口

### 5.1 获取个人资料
```
GET /user/profile
```
**Response:** `User`

### 5.2 更新个人资料
```
PUT /user/profile
```
**Request:** `{ "username": "新名称" }`
**Response:** `User`

### 5.3 注销账号
```
DELETE /user/account
```
**Response (首次请求):**
```json
{ "message": "注销申请已提交",  "status": "pending",  "cooldown_days": 15 }
```
**Response (二次确认):**
```json
{ "message": "账号已注销",  "status": "success" }
```

### 5.4 举报内容
```
POST /user/report
```
**Request:**
```json
{ "target_type": "activity",  "target_id": 1,  "reason": "违规内容" }
```
**Response:** `{ "message": "举报已提交" }`

---

## 6. 组织接口

### 6.1 获取我的组织
```
GET /org/me
```
**Response:** `Org`

### 6.2 获取组织成员
```
GET /org/me/members
```
**Response:** `[OrgMember]`

### 6.3 更新组织信息
```
PUT /org/me
```
**Request:** `{ "name": "新组织名称" }`
**Response:** `Org`

---

## 7. 订阅接口

### 7.1 获取套餐列表
```
GET /billing/plans
```
**Response:** `[Plan]`

### 7.2 获取我的权益
```
GET /billing/me/entitlements
```
**Response:** `{ "org_id": 1,  "entitlements": { "export.enabled": true } }`

### 7.3 获取我的订阅
```
GET /billing/me/subscription
```
**Response:** `{ "org_id": 1,  "subscription": { ... } }`

---

## 8. 数据分析接口

### 8.1 批量上报埋点
```
POST /analytics/events/batch
```
**Request:**
```json
{ "events": [ { "event_name": "page_view",  "properties": { ... } } ] }
```
**Response:** `{ "accepted": 10 }`

### 8.2 获取数据看板
```
GET /analytics/dashboard
```
**Response:** `{ "org_id": 1,  "date": "2023-10-01",  "metrics": { ... } }`

---

## 9. 错误码规范

### 9.1 响应结构
```json
{
  "code": "ERROR_CODE",
  "message": "用户可读的错误描述",
  "request_id": "X-Request-Id-Value"
}
```

### 9.2 通用错误码

| 错误码 | HTTP 状态码 | 含义 |
|--------|-------------|------|
| `REQ_INVALID` | 400 | 请求参数格式错误 |
| `AUTH_UNAUTHORIZED` | 401 | 未登录或 Token 无效 |
| `AUTH_FORBIDDEN` | 403 | 无权访问该资源 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突 |
| `RATE_LIMITED` | 429 | 请求频率过高 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

### 9.3 业务错误码

| 错误码 | 含义 |
|--------|------|
| `AUTH_CODE_INVALID` | 验证码错误 |
| `AUTH_CODE_EXPIRED` | 验证码已过期 |
| `AUTH_TOKEN_EXPIRED` | JWT 令牌已过期 |
| `CONTENT_SECURITY_VIOLATION` | 内容包含违规信息 |
| `ACTIVITY_FULL` | 活动名额已满 |
| `ACTIVITY_ENDED` | 活动已结束 |
| `ALREADY_REGISTERED` | 已报名过此活动 |
| `CHECKIN_CODE_INVALID` | 签到码无效 |
| `ALREADY_CHECKED_IN` | 已完成签到 |
| `PLAN_NOT_FOUND` | 套餐不存在 |
| `ENTITLEMENT_INSUFFICIENT` | 权益不足 |

### 9.4 前端处理建议
- `401`: 清除本地 Token 并跳转登录页
- `429/500`: 显示全局提示"系统繁忙"
- `400/409`: 展示具体业务冲突原因
