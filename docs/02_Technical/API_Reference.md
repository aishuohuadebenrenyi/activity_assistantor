# API Reference

## 概览
- **Base URL**: `http://localhost:9000/api` (开发环境)
- **认证方式**: Bearer Token
  - Header: `Authorization: Bearer <token>`

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
