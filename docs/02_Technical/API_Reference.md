# API Reference

> **Version**: v6.2.0 | **Last Updated**: 2026-03-15

## 1. 修订历史

| 版本号 | 修订日期 | 修订人 | 修订内容说明 |
| :--- | :--- | :--- | :--- |
| v6.1.0 | 2026-03-10 | Dev Team | 初始 API 文档 |
| v6.2.0 | 2026-03-15 | AI Assistant | 增加组织、计费、埋点及客服接口；补充幂等性 Header 说明 |

## 2. 概览
- **Base URL**: `http://localhost:9000/api` (开发环境)
- **认证方式**: Bearer Token
  - Header: `Authorization: Bearer <token>`
- **幂等控制**: 
  - Header: `Idempotency-Key: <unique_uuid>`
  - 适用接口：所有 `POST` / `PUT` / `DELETE` 接口。
  - 效果：若 24 小时内重复发送相同 Key 的请求，后端将直接返回首次执行结果。

## 1. 认证 (Auth)

### 1.1 发送验证码
发送短信验证码到指定手机号。

- **URL**: `/auth/send-code`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "phone": "13800138000"
  }
  ```
- **Response**:
  - `200 OK`: `{ "message": "验证码已发送" }`
  - `400 Bad Request`: `{ "error": "请输入手机号" }`

### 1.2 登录
使用手机号和验证码登录/注册。

- **URL**: `/auth/login`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "phone": "13800138000",
    "code": "123456"
  }
  ```
- **Response**:
  - `200 OK`:
    ```json
    {
      "token": "ey...",
      "user": { "id": 1, "phone": "138...", ... }
    }
    ```
  - `401 Unauthorized`: `{ "error": "验证码错误" }`

## 2. 活动 (Activities)

### 2.1 获取活动列表
- **URL**: `/activities/`
- **Method**: `GET`
- **Query Params**:
  - `status`: (可选) `all`, `ongoing`, `upcoming`, `ended`
  - `search`: (可选) 搜索关键词（名称或地点）
- **Response**: `200 OK` -> `[Activity]`

### 2.2 创建活动
- **URL**: `/activities/`
- **Method**: `POST`
- **Body**:
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
- **Response**: `201 Created` -> `Activity`

### 2.3 获取活动详情
- **URL**: `/activities/<id>`
- **Method**: `GET`
- **Response**: `200 OK` -> `Activity`

### 2.4 更新活动
- **URL**: `/activities/<id>`
- **Method**: `PUT`
- **Body**: (部分字段)
  ```json
  {
    "name": "新名称",
    "location": "新地点"
  }
  ```
- **Response**: `200 OK` -> `Activity`

### 2.5 删除活动
- **URL**: `/activities/<id>`
- **Method**: `DELETE`
- **Response**: `200 OK` -> `{ "message": "Activity deleted" }`

## 3. 参与者 (Participants)

### 3.1 获取报名列表
- **URL**: `/<activity_id>/participants`
- **Method**: `GET`
- **Response**: `200 OK` -> `[Registration]`

### 3.2 报名活动
- **URL**: `/<activity_id>/register`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "name": "张三",
    "phone": "13900000000"
  }
  ```
- **Response**: `201 Created` -> `Registration`

### 3.3 签到
- **URL**: `/<activity_id>/checkin`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "registration_id": 123,
    "device_info": "iPhone 14"
  }
  ```
- **Response**: `200 OK` -> `CheckinRecord`

### 3.4 取消签到
- **URL**: `/<activity_id>/checkin/<record_id>`
- **Method**: `DELETE`
- **Response**: `200 OK` -> `{ "message": "Checkin cancelled" }`

## 4. 用户 (User)

### 4.1 获取个人资料
- **URL**: `/user/profile`
- **Method**: `GET`
- **Response**: `200 OK` -> `User`

### 4.2 更新个人资料
- **URL**: `/user/profile`
- **Method**: `PUT`
- **Body**:
  ```json
  {
    "username": "New Name",
    "bio": "..."
  }
  ```
- **Response**: `200 OK` -> `User`

### 4.3 注销账号
- **URL**: `/user/account`
- **Method**: `DELETE`
- **Response**:
  - `200 OK`: `{ "message": "...", "status": "pending", "cooldown_days": 15 }` (首次请求)
  - `200 OK`: `{ "message": "...", "status": "success" }` (第二次确认)

### 4.4 举报内容
- **URL**: `/user/report`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "target_type": "activity",
    "target_id": 1,
    "reason": "违规内容"
  }
  ```
- **Response**: `200 OK` -> `{ "message": "...", "status": "success" }`

## 5. 组织 (Org)

### 5.1 获取我的组织
- **URL**: `/org/me`
- **Method**: `GET`
- **Response**: `200 OK` -> `Org`

### 5.2 获取组织成员
- **URL**: `/org/me/members`
- **Method**: `GET`
- **Response**: `200 OK` -> `[OrgMember]`

### 5.3 更新组织信息
- **URL**: `/org/me`
- **Method**: `PUT`
- **Body**: `{ "name": "新组织名称" }`
- **Response**: `200 OK` -> `Org`

## 6. 计费与订阅 (Billing)

### 6.1 获取套餐列表
- **URL**: `/billing/plans`
- **Method**: `GET`
- **Response**: `200 OK` -> `[Plan]`

### 6.2 获取我的权益
- **URL**: `/billing/me/entitlements`
- **Method**: `GET`
- **Response**: `200 OK` -> `{ "org_id": 1, "entitlements": { "export.enabled": true, ... } }`

### 6.3 获取我的订阅
- **URL**: `/billing/me/subscription`
- **Method**: `GET`
- **Response**: `200 OK` -> `{ "org_id": 1, "subscription": { ... } }`

### 6.4 手动授予订阅 (Admin)
- **URL**: `/billing/admin/manual-grant`
- **Method**: `POST`
- **Body**: `{ "plan_code": "free", "days": 30 }`
- **Response**: `200 OK` -> `{ "message": "...", "subscription_id": 1 }`

## 7. 客服支持 (Support)

### 7.1 获取客服入口
- **URL**: `/support/entry`
- **Method**: `GET`
- **Query Params**: `scene`, `platform`
- **Response**: `200 OK` -> `{ "customer_service_url": "...", "context_token": "...", "context": { ... } }`

### 7.2 记录客服会话
- **URL**: `/support/session`
- **Method**: `POST`
- **Body**: `{ "status": "opened", "entry_point": "feedback", ... }`
- **Response**: `200 OK` -> `{ "message": "ok", "session_id": 1 }`

## 8. 数据分析 (Analytics)

### 8.1 批量上报埋点
- **URL**: `/analytics/events/batch`
- **Method**: `POST`
- **Body**: `{ "events": [ { "event_name": "page_view", "properties": { ... } }, ... ] }`
- **Response**: `200 OK` -> `{ "accepted": 10 }`

### 8.2 获取数据看板
- **URL**: `/analytics/dashboard`
- **Method**: `GET`
- **Response**: `200 OK` -> `{ "org_id": 1, "date": "2023-10-01", "metrics": { ... } }`
