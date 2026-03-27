# Zentro 技术架构与业务逻辑分析报告

> **Version**: v1.0.0 | **Last Updated**: 2026-03-26

本文档对 Zentro 项目进行全面的技术架构与业务逻辑梳理分析，识别问题并制定优化方案。

---

## 一、项目架构总览

### 1.1 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Zentro 系统架构                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        前端层 (Frontend)                             │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │   │
│  │  │   iOS App       │  │  Android App    │  │  微信小程序      │     │   │
│  │  │  (uni-app x)    │  │  (uni-app x)    │  │  (uni-app x)    │     │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │   │
│  │                              │                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              跨端适配层 (adapters/platform.uts)              │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼ HTTPS                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        后端层 (Backend)                              │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    Flask Application                         │   │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │   │
│  │  │  │ Routes   │  │ Services │  │ Utils    │  │ Models   │    │   │   │
│  │  │  │ (API)    │  │ (业务)   │  │ (工具)   │  │ (数据)   │    │   │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        数据层 (Data)                                 │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │   │
│  │  │   MySQL       │  │   微信 API    │  │   阿里云 OSS  │           │   │
│  │  │   (主数据库)  │  │   (登录/分享) │  │   (文件存储)  │           │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **前端框架** | uni-app x + UTS | 跨平台开发框架，支持 iOS/Android/小程序 |
| **前端语言** | UTS (TypeScript 超集) | 类型安全，编译到原生 |
| **后端框架** | Flask | Python 轻量级 Web 框架 |
| **数据库** | MySQL | 关系型数据库 |
| **ORM** | SQLAlchemy | Python ORM 框架 |
| **认证** | JWT | JSON Web Token |
| **缓存** | 本地存储 | 前端使用 uni.getStorageSync |

### 1.3 目录结构

```
Zentro/
├── backend/                    # 后端代码
│   ├── routes/                 # API 路由
│   │   ├── activity.py         # 活动相关 API
│   │   ├── participant.py      # 参与者相关 API
│   │   ├── auth.py             # 认证相关 API
│   │   ├── user.py             # 用户相关 API
│   │   └── analytics.py        # 埋点相关 API
│   ├── services/               # 业务服务
│   │   ├── wechat_service.py   # 微信服务
│   │   ├── email_service.py    # 邮件服务
│   │   └── qrcode_service.py   # 二维码服务
│   ├── utils/                  # 工具函数
│   │   ├── auth.py             # 认证工具
│   │   ├── idempotency.py      # 幂等性控制
│   │   └── logger.py           # 日志工具
│   ├── models.py               # 数据模型
│   └── app.py                  # 应用入口
│
├── frontend/                   # 前端代码
│   ├── pages/                  # 页面组件
│   │   ├── activities/         # 首页/活动列表
│   │   ├── activity/           # 活动相关页面
│   │   ├── auth/               # 登录页面
│   │   ├── profile/            # 个人中心
│   │   └── user/               # 用户相关页面
│   ├── store/                  # 状态管理
│   ├── utils/                  # 工具函数
│   │   ├── request.uts         # 网络请求封装
│   │   ├── config.uts          # 配置管理
│   │   ├── analytics/          # 埋点相关
│   │   └── adapters/           # 跨端适配
│   └── mock/                   # Mock 数据
│
└── docs/                       # 文档
```

---

## 二、核心业务流程分析

### 2.1 用户认证流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           用户认证流程                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐                                                            │
│  │  打开应用   │                                                            │
│  └──────┬──────┘                                                            │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐     ┌─────────────┐                                       │
│  │ 检查本地    │────▶│ 有 Token?   │                                       │
│  │ Token       │     └──────┬──────┘                                       │
│  └─────────────┘            │                                               │
│                    ┌────────┴────────┐                                      │
│                    ▼                 ▼                                      │
│              ┌──────────┐      ┌──────────┐                                │
│              │ 是       │      │ 否       │                                │
│              └────┬─────┘      └────┬─────┘                                │
│                   │                 │                                       │
│                   ▼                 ▼                                       │
│            ┌────────────┐    ┌────────────┐                                │
│            │ 验证 Token │    │ 跳转登录页 │                                │
│            └─────┬──────┘    └─────┬──────┘                                │
│                  │                 │                                        │
│           ┌──────┴──────┐          │                                        │
│           ▼             ▼          │                                        │
│     ┌──────────┐  ┌──────────┐     │                                        │
│     │ 有效     │  │ 无效     │     │                                        │
│     └────┬─────┘  └────┬─────┘     │                                        │
│          │             │           │                                        │
│          ▼             └───────────┤                                        │
│    ┌──────────┐                    │                                        │
│    │ 进入首页 │                    ▼                                        │
│    └──────────┘            ┌───────────────┐                               │
│                            │ 选择登录方式  │                               │
│                            └───────┬───────┘                               │
│                    ┌───────────────┼───────────────┐                        │
│                    ▼               ▼               ▼                        │
│              ┌──────────┐   ┌──────────┐   ┌──────────┐                    │
│              │ 手机号   │   │ 微信     │   │ Apple    │                    │
│              │ 验证码   │   │ 登录     │   │ 登录     │                    │
│              └────┬─────┘   └────┬─────┘   └────┬─────┘                    │
│                   │              │              │                           │
│                   └──────────────┼──────────────┘                           │
│                                  ▼                                          │
│                           ┌───────────┐                                    │
│                           │ 获取 JWT  │                                    │
│                           │ 存储本地  │                                    │
│                           └─────┬─────┘                                    │
│                                 │                                          │
│                                 ▼                                          │
│                           ┌───────────┐                                    │
│                           │ 进入首页  │                                    │
│                           └───────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 活动管理流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           活动管理流程                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  【创建活动 - App端】                                                        │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │ 点击创建│────▶│ 填写表单│────▶│ 内容审核│────▶│ 创建成功│              │
│  │ 按钮    │     │         │     │ (微信)  │     │         │              │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘              │
│                        │              │                                    │
│                        │              ▼                                    │
│                        │        ┌──────────┐                              │
│                        │        │ 违规拒绝 │                              │
│                        │        └──────────┘                              │
│                        │                                                    │
│  【编辑活动 - App端】                                                        │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │ 进入详情│────▶│ 点击编辑│────▶│ 修改内容│────▶│ 保存成功│              │
│  │ 页面    │     │ 按钮    │     │         │     │         │              │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘              │
│                                                                             │
│  【删除活动 - App端】                                                        │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                              │
│  │ 点击删除│────▶│ 确认删除│────▶│ 级联删除│                              │
│  │ 按钮    │     │         │     │ 相关数据│                              │
│  └─────────┘     └─────────┘     └─────────┘                              │
│                                                                             │
│  【查看活动 - 全平台】                                                       │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                              │
│  │ 浏览列表│────▶│ 查看详情│────▶│ 浏览量+1│                              │
│  │         │     │         │     │         │                              │
│  └─────────┘     └─────────┘     └─────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 报名与签到流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         报名与签到流程                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  【报名活动 - 小程序端】                                                     │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │ 查看活动│────▶│ 点击报名│────▶│ 填写信息│────▶│ 报名成功│              │
│  │ 详情    │     │ 按钮    │     │         │     │         │              │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘              │
│                        │                                                    │
│                        ▼                                                    │
│                  ┌───────────┐                                              │
│                  │ 生成电子票│                                              │
│                  │ (二维码)  │                                              │
│                  └───────────┘                                              │
│                                                                             │
│  【签到核销 - App端】                                                        │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │ 进入签到│────▶│ 扫描二维码│────▶│ 验证签到码│────▶│ 签到成功│            │
│  │ 管理页  │     │ 或手动   │     │         │     │         │              │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘              │
│                        │              │                                    │
│                        │              ▼                                    │
│                        │        ┌──────────┐                              │
│                        │        │ 签到失败 │                              │
│                        │        │ (无效/重复)│                             │
│                        │        └──────────┘                              │
│                                                                             │
│  【取消报名 - 小程序端】                                                     │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                              │
│  │ 我的报名│────▶│ 点击取消│────▶│ 取消成功│                              │
│  │ 列表    │     │ 按钮    │     │         │                              │
│  └─────────┘     └─────────┘     └─────────┘                              │
│                        │                                                    │
│                        ▼                                                    │
│                  ┌───────────┐                                              │
│                  │ 已签到不可│                                              │
│                  │ 取消      │                                              │
│                  └───────────┘                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、数据流转分析

### 3.1 数据模型关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           数据模型关系图                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────┐          │
│  │    User     │         │  Activity   │         │Registration │          │
│  ├─────────────┤         ├─────────────┤         ├─────────────┤          │
│  │ id          │◀───────▶│ id          │◀───────▶│ id          │          │
│  │ phone       │  创建    │ user_id     │  报名    │ activity_id │          │
│  │ username    │         │ name        │         │ user_id     │          │
│  │ avatar_url  │         │ type        │         │ name        │          │
│  │ bio         │         │ start_time  │         │ phone       │          │
│  │ is_certified│         │ end_time    │         │ created_at  │          │
│  │ created_at  │         │ location    │         └──────┬──────┘          │
│  └─────────────┘         │ description │                │                 │
│                          │ capacity    │                │                 │
│                          │ views_count │                ▼                 │
│                          │ host_phone  │         ┌─────────────┐          │
│                          │ host_wechat │         │CheckinRecord│          │
│                          └─────────────┘         ├─────────────┤          │
│                                                  │ id          │          │
│                          ┌─────────────┐         │ registration│          │
│                          │   Report    │         │ activity_id │          │
│                          ├─────────────┤         │ checkin_time│          │
│                          │ id          │         └─────────────┘          │
│                          │ activity_id │                                   │
│                          │ user_id     │                                   │
│                          │ reason      │                                   │
│                          │ detail      │                                   │
│                          └─────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 API 数据流转

| API 端点 | 方法 | 数据流向 | 说明 |
|----------|------|----------|------|
| `/api/auth/login` | POST | 前端 → 后端 | 发送验证码，获取 Token |
| `/api/auth/verify` | POST | 前端 → 后端 | 验证登录，返回 JWT |
| `/api/activities` | GET | 后端 → 前端 | 获取活动列表 |
| `/api/activities` | POST | 前端 → 后端 | 创建活动 |
| `/api/activities/<id>` | GET | 后端 → 前端 | 获取活动详情 |
| `/api/activities/<id>` | PUT | 前端 → 后端 | 更新活动 |
| `/api/activities/<id>/register` | POST | 前端 → 后端 | 报名活动 |
| `/api/activities/<id>/checkin` | POST | 前端 → 后端 | 签到核销 |

---

## 四、问题识别与分析

### 4.1 业务逻辑问题

| 问题编号 | 问题描述 | 影响范围 | 严重程度 |
|----------|----------|----------|----------|
| B01 | **报名重复校验逻辑冗余**：同时检查 user_id 和 phone，可能导致边界情况 | participant.py | 中 |
| B02 | **活动状态计算缺失**：status 字段未在模型中定义，依赖前端判断 | models.py | 高 |
| B03 | **签到码过期机制缺失**：签到二维码无有效期，存在安全隐患 | qrcode_service.py | 中 |
| B04 | **浏览量并发问题**：views_count +1 操作无并发控制 | activity.py | 低 |
| B05 | **联系方式可见性逻辑分散**：show_phone/show_wechat 判断在多处重复 | activity.py, detail.uvue | 低 |

### 4.2 技术架构问题

| 问题编号 | 问题描述 | 影响范围 | 严重程度 |
|----------|----------|----------|----------|
| T01 | **access_token 未缓存**：每次调用微信 API 都重新获取 | wechat_service.py | 高 |
| T02 | **错误响应格式不统一**：部分使用 `{error: ...}`，部分使用标准格式 | routes/*.py | 中 |
| T03 | **缺少请求日志追踪**：API 请求无唯一标识，难以排查问题 | app.py | 中 |
| T04 | **前端状态管理简单**：使用简单的响应式对象，缺少状态持久化策略 | store/index.uts | 低 |
| T05 | **离线队列无持久化**：应用关闭后队列丢失 | offline_queue.uts | 中 |

### 4.3 平台兼容性问题

| 问题编号 | 问题描述 | 影响平台 | 严重程度 |
|----------|----------|----------|----------|
| P01 | **条件编译分散**：`#ifdef MP-WEIXIN` 等条件编译分散在多处 | 全平台 | 低 |
| P02 | **Android 平台未适配**：platform.uts 中 Android 归为 unknown | Android | 中 |
| P03 | **小程序分享功能差异**：小程序使用 onShareAppMessage，App 使用自定义分享 | 小程序/App | 低 |
| P04 | **键盘高度监听差异**：iOS 和小程序键盘事件行为不一致 | iOS/小程序 | 低 |
| P05 | **安全区域适配**：刘海屏/灵动岛适配需验证 | iOS | 低 |

### 4.4 代码质量问题

| 问题编号 | 问题描述 | 影响范围 | 严重程度 |
|----------|----------|----------|----------|
| C01 | **异常处理不完善**：多处 except 只打印日志，未做恢复处理 | 多处 | 中 |
| C02 | **硬编码配置**：部分配置硬编码在代码中 | config.uts, wechat_service.py | 低 |
| C03 | **注释不一致**：部分文件注释详细，部分缺少注释 | 多处 | 低 |
| C04 | **类型定义不完整**：UTS 文件中部分类型使用 any | 多处 | 低 |
| C05 | **测试覆盖不足**：单元测试仅覆盖部分模块 | tests/ | 中 |

---

## 五、优化方案

### 5.1 业务逻辑优化

#### B01: 报名重复校验优化

**当前实现：**
```python
# participant.py - 当前实现
if user.id:
    existing_by_user = Registration.query.filter_by(activity_id=activity_id, user_id=user.id).first()
    if existing_by_user:
        return jsonify({'error': '您已经报名过此活动'}), 400

existing_by_phone = Registration.query.filter_by(activity_id=activity_id, phone=phone).first()
if existing_by_phone:
    return jsonify({'error': '该手机号已报名过此活动'}), 400
```

**优化方案：**
```python
def _check_duplicate_registration(activity_id: int, user_id: int, phone: str) -> tuple[bool, str]:
    """
    检查重复报名（统一校验逻辑）。
    
    优先级：
    1. user_id 匹配（已登录用户）
    2. phone 匹配（同一手机号）
    
    返回：
    - (is_duplicate, error_message)
    """
    if user_id:
        existing = Registration.query.filter(
            Registration.activity_id == activity_id,
            Registration.user_id == user_id
        ).first()
        if existing:
            return True, '您已经报名过此活动'
    
    existing = Registration.query.filter(
        Registration.activity_id == activity_id,
        Registration.phone == phone
    ).first()
    if existing:
        return True, '该手机号已报名过此活动'
    
    return False, ''
```

#### B02: 活动状态计算优化

**优化方案：在模型中添加计算属性**

```python
# models.py - Activity 模型优化
class Activity(db.Model):
    # ... 现有字段 ...
    
    @property
    def status(self) -> str:
        """
        计算活动状态。
        
        状态定义：
        - upcoming: 未开始（start_time > now）
        - ongoing: 进行中（start_time <= now < end_time）
        - ended: 已结束（end_time <= now 或手动结束）
        """
        now = datetime.utcnow()
        
        if self.start_time and self.start_time > now:
            return 'upcoming'
        
        if self.end_time and self.end_time <= now:
            return 'ended'
        
        if self.start_time and self.start_time <= now:
            if self.end_time:
                return 'ongoing' if now < self.end_time else 'ended'
            return 'ongoing'
        
        return 'upcoming'
    
    def to_dict(self, **kwargs):
        result = {
            'id': self.id,
            'name': self.name,
            # ... 其他字段 ...
            'status': self.status,  # 添加计算状态
        }
        # ... 其余逻辑 ...
        return result
```

#### B03: 签到码过期机制

**优化方案：**

```python
# services/qrcode_service.py

SIGNATURE_EXPIRY_SECONDS = 300  # 5分钟有效期

def verify_signature(activity_id: int, registration_id: int, timestamp: int, signature: str) -> tuple[bool, str]:
    """
    验证签到码签名（含过期检查）。
    
    返回：
    - (is_valid, error_message)
    """
    now = int(time.time())
    
    # 检查是否过期
    if now - timestamp > SIGNATURE_EXPIRY_SECONDS:
        return False, '签到码已过期，请刷新后重试'
    
    # 检查时间戳是否在未来
    if timestamp > now + 60:  # 允许 60 秒时钟偏差
        return False, '签到码无效'
    
    # 验证签名
    expected = generate_signature(activity_id, registration_id, timestamp)
    if signature != expected:
        return False, '签到码签名无效'
    
    return True, ''
```

### 5.2 技术架构优化

#### T01: access_token 缓存优化

**优化方案：**

```python
# services/wechat_service.py

import time
from threading import Lock

class WeChatService:
    _access_token_cache: dict = {
        'token': None,
        'expires_at': 0
    }
    _token_lock = Lock()
    
    @classmethod
    def get_access_token(cls) -> str | None:
        """
        获取微信 access_token（带缓存）。
        
        缓存策略：
        - 有效期 7200 秒，提前 300 秒刷新
        - 使用线程锁防止并发请求
        """
        now = time.time()
        
        # 检查缓存是否有效
        if cls._access_token_cache['token'] and cls._access_token_cache['expires_at'] > now:
            return cls._access_token_cache['token']
        
        # 加锁防止并发
        with cls._token_lock:
            # 双重检查
            if cls._access_token_cache['token'] and cls._access_token_cache['expires_at'] > now:
                return cls._access_token_cache['token']
            
            # 请求新 token
            token = cls._fetch_access_token()
            if token:
                cls._access_token_cache['token'] = token
                cls._access_token_cache['expires_at'] = now + 7200 - 300  # 提前 5 分钟过期
            
            return token
    
    @classmethod
    def _fetch_access_token(cls) -> str | None:
        """实际请求微信 API 获取 token。"""
        # ... 现有获取逻辑 ...
```

#### T02: 错误响应格式统一

**优化方案：创建统一响应工具**

```python
# utils/response.py

from flask import jsonify
from typing import Any, Optional

class APIResponse:
    """统一 API 响应格式。"""
    
    @staticmethod
    def success(data: Any = None, message: str = 'success', **kwargs):
        """成功响应。"""
        response = {
            'success': True,
            'message': message,
            'data': data,
            **kwargs
        }
        return jsonify(response), 200
    
    @staticmethod
    def error(message: str, code: str = 'UNKNOWN_ERROR', status: int = 400, **kwargs):
        """错误响应。"""
        response = {
            'success': False,
            'error': {
                'code': code,
                'message': message,
                **kwargs
            }
        }
        return jsonify(response), status
    
    @staticmethod
    def created(data: Any = None, message: str = 'created'):
        """创建成功响应。"""
        return APIResponse.success(data, message, status=201)
    
    @staticmethod
    def not_found(message: str = 'Resource not found'):
        """资源不存在响应。"""
        return APIResponse.error(message, 'NOT_FOUND', 404)
    
    @staticmethod
    def unauthorized(message: str = 'Unauthorized'):
        """未授权响应。"""
        return APIResponse.error(message, 'UNAUTHORIZED', 401)
    
    @staticmethod
    def forbidden(message: str = 'Forbidden'):
        """禁止访问响应。"""
        return APIResponse.error(message, 'FORBIDDEN', 403)

# 使用示例
@activity_bp.route('/<int:id>', methods=['GET'])
def get_activity(id):
    activity = Activity.query.get(id)
    if not activity:
        return APIResponse.not_found('活动不存在')
    return APIResponse.success(activity.to_dict())
```

#### T03: 请求日志追踪

**优化方案：添加请求中间件**

```python
# app.py

import uuid
import time

@app.before_request
def before_request():
    """请求前处理：生成请求 ID，记录开始时间。"""
    g.request_id = str(uuid.uuid4())[:8]
    g.start_time = time.time()
    
    logger.info(f"[{g.request_id}] --> {request.method} {request.path}")

@app.after_request
def after_request(response):
    """请求后处理：记录响应时间和状态。"""
    duration = (time.time() - g.start_time) * 1000
    
    logger.info(
        f"[{g.request_id}] <-- {response.status_code} "
        f"({duration:.2f}ms)"
    )
    
    # 添加请求 ID 到响应头
    response.headers['X-Request-ID'] = g.request_id
    return response
```

### 5.3 平台兼容性优化

#### P01: 条件编译统一管理

**优化方案：创建平台适配层**

```typescript
// adapters/platform.uts - 扩展平台适配

export type ClientPlatform = 'mp_weixin' | 'ios' | 'android' | 'h5' | 'unknown'

export const platform = {
  /**
   * 获取当前平台
   */
  get current(): ClientPlatform {
    return getClientPlatform()
  },
  
  /**
   * 是否为小程序
   */
  get isMiniProgram(): boolean {
    // #ifdef MP-WEIXIN
    return true
    // #endif
    return false
  },
  
  /**
   * 是否为 App
   */
  get isApp(): boolean {
    // #ifdef APP-PLUS
    return true
    // #endif
    return false
  },
  
  /**
   * 是否为 iOS
   */
  get isIOS(): boolean {
    // #ifdef APP-PLUS
    const sys = uni.getSystemInfoSync()
    return (sys as any).platform === 'ios'
    // #endif
    return false
  },
  
  /**
   * 是否为 Android
   */
  get isAndroid(): boolean {
    // #ifdef APP-PLUS
    const sys = uni.getSystemInfoSync()
    return (sys as any).platform === 'android'
    // #endif
    return false
  },
  
  /**
   * 是否支持创建活动（仅 App）
   */
  get canCreateActivity(): boolean {
    return this.isApp
  },
  
  /**
   * 是否支持报名活动（仅小程序）
   */
  get canRegisterActivity(): boolean {
    return this.isMiniProgram
  },
  
  /**
   * 是否支持签到管理（仅 App）
   */
  get canManageCheckin(): boolean {
    return this.isApp
  }
}
```

#### P02: Android 平台适配

**优化方案：**

```typescript
// adapters/platform.uts - 修复 Android 识别

export const getClientPlatform = (): ClientPlatform => {
  let p: ClientPlatform = 'unknown'
  
  // #ifdef MP-WEIXIN
  p = 'mp_weixin'
  // #endif
  
  // #ifdef APP-PLUS
  const sys = uni.getSystemInfoSync()
  const platform = (sys as any).platform
  
  if (platform === 'ios') {
    p = 'ios'
  } else if (platform === 'android') {
    p = 'android'
  } else {
    // 兜底：通过 UA 判断
    const ua = (sys as any).ua || ''
    if (ua.toLowerCase().includes('android')) {
      p = 'android'
    } else if (ua.toLowerCase().includes('iphone') || ua.toLowerCase().includes('ipad')) {
      p = 'ios'
    }
  }
  // #endif
  
  // #ifdef H5
  p = 'h5'
  // #endif
  
  return p
}
```

### 5.4 代码质量优化

#### C01: 异常处理优化

**优化方案：创建统一异常处理**

```python
# utils/exceptions.py

class AppException(Exception):
    """应用基础异常。"""
    
    def __init__(self, message: str, code: str = 'APP_ERROR', status: int = 400):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(message)


class ValidationError(AppException):
    """校验错误。"""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, 'VALIDATION_ERROR', 400)


class NotFoundError(AppException):
    """资源不存在。"""
    
    def __init__(self, resource: str = 'Resource'):
        super().__init__(f'{resource}不存在', 'NOT_FOUND', 404)


class ForbiddenError(AppException):
    """禁止访问。"""
    
    def __init__(self, message: str = '没有权限访问'):
        super().__init__(message, 'FORBIDDEN', 403)


# app.py - 全局异常处理
@app.errorhandler(AppException)
def handle_app_exception(e: AppException):
    logger.warning(f"App exception: {e.code} - {e.message}")
    return APIResponse.error(e.message, e.code, e.status)


@app.errorhandler(Exception)
def handle_exception(e: Exception):
    logger.error(f"Unexpected exception: {str(e)}", exc_info=True)
    return APIResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)
```

---

## 六、优化实施计划

### 6.1 优先级排序

| 优先级 | 问题编号 | 优化内容 | 预计工时 |
|--------|----------|----------|----------|
| P0 | T01 | access_token 缓存 | 2h |
| P0 | B02 | 活动状态计算 | 1h |
| P1 | T02 | 错误响应格式统一 | 4h |
| P1 | T03 | 请求日志追踪 | 2h |
| P1 | B03 | 签到码过期机制 | 2h |
| P2 | P02 | Android 平台适配 | 2h |
| P2 | P01 | 条件编译统一 | 3h |
| P2 | C01 | 异常处理优化 | 4h |
| P3 | B01 | 报名校验优化 | 1h |
| P3 | T05 | 离线队列持久化 | 3h |

### 6.2 实施步骤

1. **第一阶段（P0）**：修复关键问题
   - access_token 缓存
   - 活动状态计算

2. **第二阶段（P1）**：架构优化
   - 错误响应格式统一
   - 请求日志追踪
   - 签到码过期机制

3. **第三阶段（P2）**：平台兼容
   - Android 平台适配
   - 条件编译统一
   - 异常处理优化

4. **第四阶段（P3）**：持续改进
   - 报名校验优化
   - 离线队列持久化
   - 测试覆盖完善

---

## 七、测试验证方案

### 7.1 单元测试

```python
# tests/test_activity_status.py

import pytest
from datetime import datetime, timedelta
from models import Activity

class TestActivityStatus:
    
    def test_upcoming_status(self):
        """测试未开始状态。"""
        activity = Activity(
            start_time=datetime.utcnow() + timedelta(days=1)
        )
        assert activity.status == 'upcoming'
    
    def test_ongoing_status(self):
        """测试进行中状态。"""
        activity = Activity(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(hours=1)
        )
        assert activity.status == 'ongoing'
    
    def test_ended_status(self):
        """测试已结束状态。"""
        activity = Activity(
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow() - timedelta(hours=1)
        )
        assert activity.status == 'ended'
```

### 7.2 集成测试

```python
# tests/test_registration.py

class TestRegistration:
    
    def test_duplicate_registration_by_user(self, client, auth_header):
        """测试同一用户重复报名。"""
        # 第一次报名
        response = client.post('/api/activities/1/register',
            json={'name': '测试', 'phone': '13800138000'},
            headers=auth_header
        )
        assert response.status_code == 201
        
        # 第二次报名
        response = client.post('/api/activities/1/register',
            json={'name': '测试', 'phone': '13900139000'},
            headers=auth_header
        )
        assert response.status_code == 400
```

### 7.3 平台兼容性测试

| 测试项 | iOS | Android | 小程序 | H5 |
|--------|-----|---------|--------|-----|
| 登录流程 | ✅ | ✅ | ✅ | - |
| 活动列表 | ✅ | ✅ | ✅ | ✅ |
| 创建活动 | ✅ | ✅ | ❌ | - |
| 报名活动 | ❌ | ❌ | ✅ | - |
| 签到管理 | ✅ | ✅ | ❌ | - |
| 分享功能 | ✅ | ✅ | ✅ | - |

---

## 八、相关文档

- [技术架构文档](./Architecture.md)
- [API 参考文档](./API_Reference.md)
- [埋点需求规格说明书](./Analytics_Requirements.md)
- [功能交互分析](../04_Analysis/Function_Interaction_Analysis.md)
