# Backend for Activity Assistant

## Prerequisites
- Python 3.9+
- MySQL (Optional, defaults to SQLite for dev)

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Mac/Linux
   # venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configuration:
   - Copy `config.py` if needed or set environment variables.
   - Default uses SQLite `app.db`.

## Running

Run from the project root:
```bash
python run.py
```

The API will be available at `http://localhost:9000`.

## API 接口概览

所有接口以 `/api` 开头。

### 🔑 认证与账号 (Auth)
- `POST /auth/login`: 手机号 + 验证码登录 (默认测试码 `123456`)
- `POST /auth/login/wechat`: 微信一键登录 (小程序端)
- `POST /auth/send-code`: 发送短信验证码 (接入 `SmsService`)

### 📅 活动管理 (Activity)
- `GET /activities`: 获取活动列表 (支持 `status` 筛选与 `search` 关键词)
- `POST /activities`: 创建新活动 (含 **微信内容安全校验**)
- `GET /activities/<id>`: 获取单个活动详情
- `PUT /activities/<id>`: 修改活动信息 (仅主办方)
- `DELETE /activities/<id>`: 删除活动 (仅主办方)
- `GET /activities/<id>/share`: 生成微信分享链接与小程序码
- `POST /activities/<id>/report`: 举报活动

### 👥 报名与核销 (Participant)
- `POST /activities/<id>/register`: 参与者报名活动
- `GET /activities/<id>/my-ticket`: 参与者获取电子票 (Base64 签到码)
- `GET /activities/<id>/participants`: 主办方查看报名名单 (含签到状态)
- `POST /activities/<id>/checkin`: 活动核销 (支持 **Base64 二维码解析** 或 `registration_id` 手动核销)
- `POST /activities/<id>/export`: 导出报名名单 (CSV 格式异步模拟发送)

## 🛡 安全机制

1.  **JWT 鉴权**: 所有私有接口需携带 `Authorization: Bearer <token>`。
2.  **内容合规**: `Activity` 的创建与更新通过 `WeChatService.check_content_security` 实时校验。
3.  **权限控制**: `auth_required` 装饰器严格限制主办方与普通用户的操作权限。
