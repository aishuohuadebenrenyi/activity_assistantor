# Zentro 埋点完整指南

> **Version**: v2.0.0 | **Last Updated**: 2026-03-26

本文档整合了 Zentro 项目所有埋点相关信息，包括埋点架构、事件定义、平台适配、配置指南及最佳实践。

---

## 一、埋点架构概述

### 1.1 当前埋点系统

项目采用**友盟+ SDK 为主、自定义上报为辅**的双轨架构：

```
┌─────────────────────────────────────────────────────────────────┐
│                      Zentro 埋点架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              友盟+ SDK（主系统）                          │   │
│  │  文件：utils/analytics/events.uts                        │   │
│  │  • 自动采集：启动、前后台、页面浏览                        │   │
│  │  • 自定义事件：用户、活动、报名、签到                       │   │
│  │  • 平台：iOS App / Android App / 微信小程序               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              自定义上报系统（辅助）                        │   │
│  │  文件：utils/analytics/index.uts, analytics.uts           │   │
│  │  • 本地缓冲队列                                          │   │
│  │  • 批量上报到后端 /analytics/events                       │   │
│  │  • 离线缓存机制                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 埋点文件清单

| 文件路径 | 功能说明 | 状态 |
|----------|----------|------|
| `utils/analytics/events.uts` | 友盟+ SDK 核心实现，事件枚举定义 | 主要 |
| `utils/analytics/umeng.uts` | 友盟+ SDK 导出封装 | 主要 |
| `utils/analytics/page-tracker.uts` | 页面自动追踪工具 | 辅助 |
| `utils/analytics/index.uts` | 自定义 Analytics 类 | 辅助 |
| `utils/analytics.uts` | 简化版埋点工具 logEvent | 辅助 |

### 1.3 两套系统对比

| 特性 | 友盟+ SDK | 自定义上报 |
|------|-----------|------------|
| 数据接收方 | 友盟+ 云端 | 自有后端 |
| 实时性 | 延迟约 1 小时 | 近实时 |
| 数据保留 | 7 天（免费版） | 永久 |
| 分析能力 | 友盟+ 控制台 | 自定义查询 |
| 离线支持 | SDK 内置 | 手动实现 |
| 敏感数据 | 需手动脱敏 | 自动脱敏 |

---

## 二、埋点事件定义

### 2.1 事件分类

```
埋点事件
├── 自动采集事件（友盟+ SDK 自动触发）
│   ├── app_launch      应用启动
│   ├── app_show        应用前台
│   ├── app_hide        应用后台
│   └── page_view       页面浏览
│
├── 用户事件
│   ├── user_register       用户注册
│   ├── user_login          用户登录
│   ├── user_logout         用户登出
│   ├── user_delete_request 删除请求
│   └── user_delete_complete 删除完成
│
├── 活动事件
│   ├── activity_create_start   开始创建
│   ├── activity_create_submit  提交创建
│   ├── activity_create_success 创建成功
│   ├── activity_create_fail    创建失败
│   ├── activity_edit           编辑活动
│   ├── activity_delete         删除活动
│   ├── activity_view           查看活动
│   ├── activity_share          分享活动
│   └── activity_report         举报活动
│
├── 报名事件
│   ├── registration_click      点击报名
│   ├── registration_confirm    确认报名
│   ├── registration_success    报名成功
│   ├── registration_fail       报名失败
│   ├── registration_cancel     取消报名
│   └── registration_ticket_view 查看凭证
│
├── 签到事件
│   ├── checkin_scan        扫码签到
│   ├── checkin_scan_success 扫码成功
│   ├── checkin_scan_fail   扫码失败
│   ├── checkin_manual      手动签到
│   ├── checkin_success     签到成功
│   └── checkin_cancel      取消签到
│
├── 其他事件
│   ├── export_submit       导出提交
│   ├── export_success      导出成功
│   ├── feedback_submit     反馈提交
│   ├── profile_edit        资料编辑
│   ├── theme_change        主题切换
│   └── notification_setting 通知设置
│
└── 错误事件
    ├── api_error           API错误
    ├── form_validation_error 表单验证错误
    ├── permission_denied   权限拒绝
    └── network_error       网络错误
```

### 2.2 事件枚举定义

```typescript
// utils/analytics/events.uts

export enum AnalyticsEvent {
  // 应用事件
  APP_LAUNCH = 'app_launch',
  APP_SHOW = 'app_show',
  APP_HIDE = 'app_hide',
  PAGE_VIEW = 'page_view',
  PAGE_LEAVE = 'page_leave',
  APP_CRASH = 'app_crash',
  
  // 用户事件
  USER_REGISTER = 'user_register',
  USER_LOGIN = 'user_login',
  USER_LOGOUT = 'user_logout',
  USER_DELETE_REQUEST = 'user_delete_request',
  USER_DELETE_COMPLETE = 'user_delete_complete',
  
  // 活动事件
  ACTIVITY_CREATE_START = 'activity_create_start',
  ACTIVITY_CREATE_SUBMIT = 'activity_create_submit',
  ACTIVITY_CREATE_SUCCESS = 'activity_create_success',
  ACTIVITY_CREATE_FAIL = 'activity_create_fail',
  ACTIVITY_CREATE_VALIDATION_FAIL = 'activity_create_validation_fail',
  ACTIVITY_EDIT = 'activity_edit',
  ACTIVITY_DELETE = 'activity_delete',
  ACTIVITY_VIEW = 'activity_view',
  ACTIVITY_SHARE = 'activity_share',
  ACTIVITY_REPORT = 'activity_report',
  
  // 报名事件
  REGISTRATION_CLICK = 'registration_click',
  REGISTRATION_CONFIRM = 'registration_confirm',
  REGISTRATION_SUCCESS = 'registration_success',
  REGISTRATION_FAIL = 'registration_fail',
  REGISTRATION_CANCEL = 'registration_cancel',
  REGISTRATION_TICKET_VIEW = 'registration_ticket_view',
  
  // 签到事件
  CHECKIN_SCAN = 'checkin_scan',
  CHECKIN_SCAN_SUCCESS = 'checkin_scan_success',
  CHECKIN_SCAN_FAIL = 'checkin_scan_fail',
  CHECKIN_MANUAL = 'checkin_manual',
  CHECKIN_SUCCESS = 'checkin_success',
  CHECKIN_CANCEL = 'checkin_cancel',
  
  // 其他事件
  EXPORT_SUBMIT = 'export_submit',
  EXPORT_SUCCESS = 'export_success',
  FEEDBACK_SUBMIT = 'feedback_submit',
  PROFILE_EDIT = 'profile_edit',
  THEME_CHANGE = 'theme_change',
  NOTIFICATION_SETTING = 'notification_setting',
  
  // 错误事件
  API_ERROR = 'api_error',
  FORM_VALIDATION_ERROR = 'form_validation_error',
  PERMISSION_DENIED = 'permission_denied',
  NETWORK_ERROR = 'network_error',
  
  // 交互事件
  CLICK_CREATE_BUTTON = 'click_create_button',
  CLICK_CHECKIN_MANAGE = 'click_checkin_manage',
  COPY_LINK = 'copy_link',
  SAVE_POSTER = 'save_poster'
}
```

### 2.3 页面名称定义

```typescript
// utils/analytics/umeng.uts

export const PAGE_NAMES: Record<string, string> = {
  'pages/activities/activities': 'activities',
  'pages/activity/create/create': 'create_activity',
  'pages/activity/detail/detail': 'activity_detail',
  'pages/activity/participants/participants': 'participants',
  'pages/activity/share/share': 'share',
  'pages/activity/success/success': 'success',
  'pages/activity/ticket/ticket': 'ticket',
  'pages/profile/profile': 'profile',
  'pages/profile/edit/edit': 'profile_edit',
  'pages/profile/feedback/feedback': 'feedback',
  'pages/auth/login': 'login',
  'pages/user/my-activities/my-activities': 'my_activities',
  'pages/user/created-activities/created-activities': 'created_activities',
  'pages/about/about': 'about',
  'pages/webview/webview': 'webview'
}
```

---

## 三、平台适配分析

### 3.1 小程序端 vs App 端埋点需求

| 维度 | 微信小程序 | iOS/Android App |
|------|------------|-----------------|
| SDK | umtrack-wx | plus.umeng |
| 初始化 | 手动 require | manifest.json 配置 |
| 用户标识 | OpenID / UnionID | 设备ID / 用户ID |
| 主要功能 | 报名、查看凭证 | 创建活动、签到管理 |
| 页面追踪 | trackPageStart/End | beginLogPageView/endLogPageView |

### 3.2 是否需要区分平台？

**结论：不需要为不同平台定义不同事件**

理由：
1. 友盟+ 免费版支持多平台数据分离
2. 同一 AppKey 下可通过 `platform` 属性区分
3. 统一事件定义便于跨平台漏斗分析
4. 减少维护成本

### 3.3 平台适配代码

```typescript
// utils/analytics/events.uts

class UmengAnalytics {
  init(): void {
    // #ifdef MP-WEIXIN
    this.initWechat();
    // #endif
    
    // #ifdef APP-PLUS
    this.initApp();
    // #endif
  }
  
  // #ifdef MP-WEIXIN
  private initWechat(): void {
    const uma = require('umtrack-wx');
    uma.init({
      appKey: UMENG_CONFIG.wechat_appkey,
      useOpenid: true,
      autoGetOpenid: true,
      debug: UMENG_CONFIG.debug
    });
  }
  // #endif
  
  // #ifdef APP-PLUS
  private initApp(): void {
    // App 端通过 manifest.json 配置，此处无需额外初始化
  }
  // #endif
  
  track(event: string, properties: Record<string, any>): void {
    // #ifdef MP-WEIXIN
    const uma = require('umtrack-wx');
    uma.trackEvent(event, properties);
    // #endif
    
    // #ifdef APP-PLUS
    plus.umeng.trackEvent(event, JSON.stringify(properties));
    // #endif
  }
}
```

---

## 四、友盟+ 免费服务配置

### 4.1 免费版限制

| 限制项 | 免费版 | 付费版 |
|--------|--------|--------|
| 事件数量 | 无限制 | 无限制 |
| 自定义属性 | 每事件 100 个 | 每事件 500 个 |
| 数据保留 | 7 天 | 90 天+ |
| 实时性 | 延迟约 1 小时 | 近实时 |
| 漏斗分析 | 支持 | 高级 |
| 留存分析 | 支持 | 高级 |

### 4.2 配置步骤

#### 步骤 1：注册友盟+ 账号

1. 访问 [友盟+ 官网](https://www.umeng.com/)
2. 注册账号并登录
3. 进入【U-App】产品

#### 步骤 2：创建应用

需要创建 **3 个应用**（分别对应 3 个平台）：

| 平台 | 应用名称 | AppKey 用途 |
|------|----------|-------------|
| iOS | Zentro iOS | ios_appkey |
| Android | Zentro Android | android_appkey |
| 微信小程序 | Zentro 微信小程序 | wechat_appkey |

#### 步骤 3：获取 AppKey

每个应用创建后会获得一个 AppKey，格式类似：`5f8a1b2c3d4e5f6g7h8i9j0k`

#### 步骤 4：配置代码

```typescript
// utils/analytics/events.uts

const UMENG_CONFIG = {
  ios_appkey: 'YOUR_IOS_APPKEY',      // 替换为实际 iOS AppKey
  android_appkey: 'YOUR_ANDROID_APPKEY', // 替换为实际 Android AppKey
  wechat_appkey: 'YOUR_WECHAT_APPKEY',   // 替换为实际微信小程序 AppKey
  debug: false  // 生产环境设为 false
}
```

#### 步骤 5：配置 App 端（manifest.json）

```json
// manifest.json

{
  "app-plus": {
    "distribute": {
      "sdkConfigs": {
        "statics": {
          "umeng": {
            "appid": "YOUR_ANDROID_APPKEY",
            "iosappid": "YOUR_IOS_APPKEY"
          }
        }
      }
    }
  }
}
```

#### 步骤 6：安装微信小程序 SDK

```bash
# 在 frontend 目录下
npm install umtrack-wx --save
# 或
yarn add umtrack-wx
```

### 4.3 需要修改的代码

#### 修改 1：替换 AppKey 占位符

```typescript
// utils/analytics/events.uts (第 10-14 行)

const UMENG_CONFIG: UmengConfig = {
  ios_appkey: 'YOUR_IOS_APPKEY',        // ← 替换
  android_appkey: 'YOUR_ANDROID_APPKEY', // ← 替换
  wechat_appkey: 'YOUR_WECHAT_APPKEY',   // ← 替换
  debug: UMENG_DEBUG
}
```

#### 修改 2：配置 manifest.json

```json
// manifest.json

{
  "app-plus": {
    "distribute": {
      "sdkConfigs": {
        "statics": {
          "umeng": {
            "appid": "YOUR_ANDROID_APPKEY",      // ← 替换
            "iosappid": "YOUR_IOS_APPKEY"        // ← 替换
          }
        }
      }
    }
  }
}
```

#### 修改 3：微信小程序 app.json

```json
// 微信小程序项目中的 app.json（如有独立配置）

{
  "plugins": {
    "umtrack-wx": {
      "version": "latest",
      "provider": "wxappid"
    }
  }
}
```

---

## 五、埋点调用指南

### 5.1 初始化

```typescript
// App.uvue

import { initAnalytics, setAnalyticsUserId } from '@/utils/analytics/umeng.uts'

export default {
  onLaunch() {
    initAnalytics();
  },
  
  onShow() {
    trackAppShow();
  },
  
  onHide() {
    trackAppHide();
  }
}
```

### 5.2 用户标识设置

```typescript
// 登录成功后设置用户ID
import { setAnalyticsUserId, trackEvent, AnalyticsEvent } from '@/utils/analytics/umeng.uts'

// 手机号登录成功
async function onPhoneLoginSuccess(user: User, isNewUser: boolean) {
  setAnalyticsUserId(user.id.toString());
  trackEvent(AnalyticsEvent.USER_LOGIN, {
    login_method: 'phone',
    is_new_user: isNewUser
  });
}

// 微信登录成功
async function onWechatLoginSuccess(user: User, isNewUser: boolean) {
  setAnalyticsUserId(user.id.toString());
  trackEvent(AnalyticsEvent.USER_LOGIN, {
    login_method: 'wechat',
    is_new_user: isNewUser
  });
}

// Apple 登录成功
async function onAppleLoginSuccess(user: User, isNewUser: boolean) {
  setAnalyticsUserId(user.id.toString());
  trackEvent(AnalyticsEvent.USER_LOGIN, {
    login_method: 'apple',
    is_new_user: isNewUser
  });
}

// 登出时清除用户ID
function onLogout() {
  trackEvent(AnalyticsEvent.USER_LOGOUT, {});
  setAnalyticsUserId(null);
}
```

### 5.3 页面追踪

```typescript
// 方式一：手动调用
import { trackPageView, trackPageLeave, AnalyticsPage } from '@/utils/analytics/umeng.uts'

export default {
  onShow() {
    trackPageView(AnalyticsPage.ACTIVITY_DETAIL);
  },
  
  onHide() {
    trackPageLeave();
  },
  
  onUnload() {
    trackPageLeave();
  }
}

// 方式二：使用页面混入
import { createPageMixin } from '@/utils/analytics/page-tracker.uts'

export default {
  ...createPageMixin('activity_detail'),
  // 其他页面逻辑
}
```

### 5.4 业务事件追踪

```typescript
import { trackEvent, AnalyticsEvent } from '@/utils/analytics/umeng.uts'

// 活动创建
function onCreateActivitySubmit(activityData: ActivityData) {
  trackEvent(AnalyticsEvent.ACTIVITY_CREATE_SUBMIT, {
    activity_type: activityData.type,
    has_location: !!activityData.location,
    has_capacity: !!activityData.capacity
  });
}

function onCreateActivitySuccess(activity: Activity) {
  trackEvent(AnalyticsEvent.ACTIVITY_CREATE_SUCCESS, {
    activity_id: activity.id,
    activity_type: activity.type,
    has_location: !!activity.location,
    has_capacity: !!activity.capacity,
    capacity: activity.capacity || 0
  });
}

// 活动报名
function onRegistrationClick(activityId: number) {
  trackEvent(AnalyticsEvent.REGISTRATION_CLICK, {
    activity_id: activityId
  });
}

function onRegistrationSuccess(activityId: number, registrationId: number) {
  trackEvent(AnalyticsEvent.REGISTRATION_SUCCESS, {
    activity_id: activityId,
    registration_id: registrationId
  });
}

// 签到
function onCheckinScan(activityId: number) {
  trackEvent(AnalyticsEvent.CHECKIN_SCAN, {
    activity_id: activityId
  });
}

function onCheckinSuccess(activityId: number, registrationId: number, method: 'scan' | 'manual') {
  trackEvent(AnalyticsEvent.CHECKIN_SUCCESS, {
    activity_id: activityId,
    registration_id: registrationId,
    checkin_method: method
  });
}

// 错误追踪
function onApiError(apiPath: string, errorCode: number | string, errorMessage: string) {
  trackEvent(AnalyticsEvent.API_ERROR, {
    api_path: apiPath,
    error_code: errorCode,
    error_message: errorMessage.substring(0, 100)
  });
}
```

---

## 六、事件属性规范

### 6.1 命名规范

```
事件命名规则：{模块}_{动作}_{结果}

示例：
├── activity_create_start      开始创建活动
├── activity_create_submit     提交创建
├── activity_create_success    创建成功
├── activity_create_fail       创建失败
├── registration_click         点击报名
├── registration_success       报名成功
└── checkin_scan_success       扫码签到成功
```

### 6.2 属性命名规范

```typescript
// 活动相关属性
interface ActivityProperties {
  activity_id: number;      // 活动ID（统一使用 activity_id）
  activity_name?: string;   // 活动名称
  activity_type?: string;   // 活动类型
  has_location?: boolean;   // 是否有地点
  has_capacity?: boolean;   // 是否有人数限制
  capacity?: number;        // 容量
}

// 用户相关属性
interface UserProperties {
  user_id: number;          // 用户ID
  login_method?: 'phone' | 'wechat' | 'apple';  // 登录方式
  is_new_user?: boolean;    // 是否新用户
}

// 页面相关属性
interface PageProperties {
  page_name: string;        // 页面名称
  page_path: string;        // 页面路径
  from_page?: string;       // 来源页面
  duration?: number;        // 停留时长（秒）
}

// 错误相关属性
interface ErrorProperties {
  error_type: string;       // 错误类型
  error_code?: string | number;  // 错误码
  error_message?: string;   // 错误信息（截取前100字符）
  api_path?: string;        // API路径
}
```

### 6.3 敏感数据处理

```typescript
// 自动脱敏的字段
const SENSITIVE_KEYS = ['phone', 'mobile', 'email', 'password', 'token', 'secret'];

// 脱敏规则
// 手机号：138****1234
// 邮箱：ab***@example.com
// 其他：******
```

---

## 七、后端埋点接收

### 7.1 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/analytics/events` | POST | 接收单个/批量事件 |
| `/analytics/events/batch` | POST | 批量接收事件 |
| `/analytics/events/query` | POST | 查询事件 |
| `/analytics/stats/daily` | GET | 每日统计 |
| `/analytics/stats/funnel` | POST | 漏斗分析 |
| `/analytics/health` | GET | 健康检查 |

### 7.2 事件数据结构

```typescript
interface TrackEvent {
  event_id: string;         // 事件唯一ID
  event_name: string;       // 事件名称
  timestamp: number;        // 时间戳（毫秒）
  user_id: string | null;   // 用户ID
  device_id: string;        // 设备ID
  session_id: string;       // 会话ID
  platform: string;         // 平台：ios/android/mp_weixin/h5
  app_version: string;      // 应用版本
  properties: object;       // 事件属性
}
```

### 7.3 后端处理逻辑

```python
# backend/routes/analytics.py

@analytics_bp.route('/events', methods=['POST'])
def receive_events():
    events = request.json.get('events', [])
    
    for event in events:
        # 1. 必填字段校验
        if not event.get('event_name'):
            continue
        
        # 2. 敏感数据脱敏
        properties = mask_sensitive_data(event.get('properties', {}))
        
        # 3. 存储到数据库
        record = EventLog(
            event_name=event['event_name'],
            user_id=event.get('user_id'),
            device_id=event.get('device_id', ''),
            platform=event.get('platform', 'unknown'),
            properties=json.dumps(properties),
            created_at=datetime.utcfromtimestamp(event['timestamp'] / 1000)
        )
        db.session.add(record)
    
    db.session.commit()
    return jsonify({'message': 'Events received'})
```

---

## 八、数据分析指南

### 8.1 关键业务漏斗

#### 漏斗一：用户登录

```
进入登录页 → 选择登录方式 → 获取验证码/授权 → 登录成功
```

事件序列：
1. `page_view` (page_name: 'login')
2. `login_get_code` / `login_wechat_authorize` / `login_apple_authorize`
3. `user_login`

#### 漏斗二：活动创建

```
点击创建 → 进入创建页 → 填写表单 → 提交 → 创建成功
```

事件序列：
1. `click_create_button`
2. `page_view` (page_name: 'create_activity')
3. `activity_create_submit`
4. `activity_create_success`

#### 漏斗三：活动报名

```
查看活动详情 → 点击报名 → 确认报名 → 报名成功
```

事件序列：
1. `activity_view`
2. `registration_click`
3. `registration_confirm`
4. `registration_success`

#### 漏斗四：签到核销

```
进入签到管理 → 扫码/手动签到 → 签到成功
```

事件序列：
1. `page_view` (page_name: 'participants')
2. `checkin_scan` / `checkin_manual`
3. `checkin_success`

### 8.2 友盟+ 控制台使用

1. 登录 [友盟+ 控制台](https://message.umeng.com/)
2. 选择对应应用
3. 查看实时数据、事件分析、漏斗分析

### 8.3 自定义查询

```bash
# 查询某日事件统计
curl -X GET "https://api.zentro.app/api/analytics/stats/daily?date=2026-03-26"

# 查询漏斗数据
curl -X POST "https://api.zentro.app/api/analytics/stats/funnel" \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {"event_name": "activity_view"},
      {"event_name": "registration_click"},
      {"event_name": "registration_success"}
    ],
    "start_time": "2026-03-01",
    "end_time": "2026-03-31"
  }'
```

---

## 九、最佳实践

### 9.1 埋点原则

1. **关键节点必埋**：登录、创建、报名、签到等核心流程
2. **错误必埋**：API 错误、表单验证错误、权限拒绝
3. **属性完整**：携带足够的上下文信息
4. **避免敏感**：不上传手机号、密码等敏感信息

### 9.2 调试技巧

```typescript
// 开启调试模式
const UMENG_DEBUG = true;

// 查看埋点日志
console.log('[Analytics] Track:', eventName, JSON.stringify(properties));
```

### 9.3 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 数据未上报 | AppKey 未配置 | 检查 UMENG_CONFIG |
| 用户ID 未关联 | 未调用 setUserId | 登录成功后调用 setAnalyticsUserId |
| 页面浏览缺失 | 未调用 pageView | 在 onShow 中调用 trackPageView |
| 事件名不规范 | 命名不一致 | 使用 AnalyticsEvent 枚举 |

---

## 十、附录

### 10.1 完整事件清单

| 事件名 | 分类 | 触发时机 | 必要属性 |
|--------|------|----------|----------|
| app_launch | 自动 | 应用启动 | is_first_launch |
| app_show | 自动 | 应用前台 | session_duration |
| app_hide | 自动 | 应用后台 | session_duration |
| page_view | 自动 | 页面显示 | page_name |
| page_leave | 自动 | 页面离开 | page_name, duration |
| user_register | 用户 | 注册成功 | register_method |
| user_login | 用户 | 登录成功 | login_method, is_new_user |
| user_logout | 用户 | 用户登出 | session_duration |
| user_delete_request | 用户 | 发起注销 | - |
| user_delete_complete | 用户 | 注销完成 | - |
| activity_create_start | 活动 | 进入创建页 | - |
| activity_create_submit | 活动 | 提交创建 | activity_type, has_location, has_capacity |
| activity_create_success | 活动 | 创建成功 | activity_id, activity_type |
| activity_create_fail | 活动 | 创建失败 | error_message |
| activity_edit | 活动 | 编辑成功 | activity_id, edit_fields |
| activity_delete | 活动 | 删除成功 | activity_id, participant_count |
| activity_view | 活动 | 查看详情 | activity_id, is_organizer, source |
| activity_share | 活动 | 分享操作 | activity_id, share_method |
| activity_report | 活动 | 提交举报 | activity_id, report_reason |
| registration_click | 报名 | 点击报名 | activity_id |
| registration_confirm | 报名 | 确认报名 | activity_id |
| registration_success | 报名 | 报名成功 | activity_id, registration_id |
| registration_fail | 报名 | 报名失败 | activity_id, error_message |
| registration_cancel | 报名 | 取消报名 | activity_id, reason |
| registration_ticket_view | 报名 | 查看凭证 | activity_id, registration_id |
| checkin_scan | 签到 | 扫码操作 | activity_id |
| checkin_scan_success | 签到 | 扫码成功 | activity_id, registration_id |
| checkin_scan_fail | 签到 | 扫码失败 | activity_id, error_message |
| checkin_manual | 签到 | 手动签到 | activity_id, registration_id |
| checkin_success | 签到 | 签到成功 | activity_id, registration_id, checkin_method |
| checkin_cancel | 签到 | 取消签到 | activity_id, registration_id |
| export_submit | 其他 | 导出提交 | activity_id, has_email |
| export_success | 其他 | 导出成功 | activity_id |
| feedback_submit | 其他 | 提交反馈 | feedback_type, has_contact |
| profile_edit | 其他 | 编辑资料 | edit_fields |
| theme_change | 其他 | 切换主题 | theme |
| notification_setting | 其他 | 通知设置 | enabled, activity_reminder, checkin_reminder |
| api_error | 错误 | API错误 | api_path, error_code, error_message |
| form_validation_error | 错误 | 表单验证失败 | form_name, error_fields |
| permission_denied | 错误 | 权限拒绝 | permission_type |
| network_error | 错误 | 网络错误 | error_type |

### 10.2 相关文档

- [友盟+ 官方文档](https://developer.umeng.com/docs/119267/detail/118584)
- [uni-app x 统计文档](https://doc.dcloud.net.cn/uni-app-x/api/statistic)
- [微信小程序统计文档](https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/statistic.html)

---

## 十一、变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v2.0.0 | 2026-03-26 | 整合所有埋点文档，统一输出 |
| v1.0.0 | 2026-03-25 | 初始版本 |
