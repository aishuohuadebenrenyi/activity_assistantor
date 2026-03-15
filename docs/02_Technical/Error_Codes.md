# API 错误码规范 (Error Codes)

本文档定义了“活动帮手”项目 API 的统一错误响应格式与各模块错误码含义。

## 1. 响应结构 (Response Format)

所有 API 在业务处理失败或参数校验失败时，应返回符合以下结构的 JSON 响应：

```json
{
  "code": "ERROR_CODE",
  "message": "用户可读的错误描述",
  "request_id": "X-Request-Id-Value"
}
```

- **code**: 唯一的业务错误标识符。
- **message**: 中文描述，可直接在前端 Toast/Alert 中展示。
- **request_id**: 后端生成的链路追踪 ID，方便日志排查。

## 2. 通用错误码 (Common Errors)

| 错误码 | HTTP 状态码 | 含义 |
| :--- | :--- | :--- |
| `REQ_INVALID` | 400 | 请求参数格式错误或缺失必填项 |
| `AUTH_UNAUTHORIZED` | 401 | 未登录或 Token 无效 |
| `AUTH_FORBIDDEN` | 403 | 登录成功但无权访问该资源 |
| `NOT_FOUND` | 404 | 资源不存在（如活动、用户不存在） |
| `CONFLICT` | 409 | 资源冲突（如重复报名、手机号已注册） |
| `RATE_LIMITED` | 429 | 请求频率过高，请稍后再试 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

## 3. 模块特定错误码

### 3.1 认证模块 (Auth)
- `AUTH_CODE_INVALID`: 验证码错误
- `AUTH_CODE_EXPIRED`: 验证码已过期
- `AUTH_TOKEN_EXPIRED`: JWT 令牌已过期

### 3.2 活动模块 (Activities)
- `CONTENT_SECURITY_VIOLATION`: 内容包含违规信息（微信安全校验未通过）
- `ACTIVITY_FULL`: 活动名额已满
- `ACTIVITY_ENDED`: 活动已结束，无法执行此操作

### 3.3 参与者模块 (Participants)
- `ALREADY_REGISTERED`: 您已经报名过此活动
- `CHECKIN_CODE_INVALID`: 签到码无效或已过期
- `ALREADY_CHECKED_IN`: 该用户已完成签到

### 3.4 计费模块 (Billing)
- `PLAN_NOT_FOUND`: 套餐不存在
- `ENTITLEMENT_INSUFFICIENT`: 权益不足（如导出次数超限）

## 4. 前端处理建议
- 拦截器统一处理 `401`：清除本地 Token 并跳转至登录页。
- 拦截器统一处理 `429/500`：显示全局温和提示（如“系统繁忙”）。
- 业务代码处理 `400/409`：通过 `message` 展示具体业务冲突原因。
