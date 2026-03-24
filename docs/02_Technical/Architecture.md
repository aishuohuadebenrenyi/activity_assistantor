# 技术架构文档

> **Version**: v1.0.0 | **Last Updated**: 2026-03-24

## 1. 技术栈

### 1.1 前端
| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 框架 | uni-app x | 基于 Vue 3 + UTS，纯原生渲染 |
| 状态管理 | Vue Reactivity | 响应式 Store |
| 网络层 | 自研封装 | JWT 注入、Mock 切换、离线队列 |
| 运行平台 | iOS / Android / 微信小程序 | 条件编译实现多端差异化 |

### 1.2 后端
| 组件 | 技术选型 | 版本 |
|------|----------|------|
| 语言 | Python | 3.9+ |
| Web 框架 | Flask | 3.0.0 |
| ORM | Flask-SQLAlchemy | 3.1.1 |
| 数据库 | SQLite(开发) / MySQL(生产) | - |
| 缓存 | 内存(开发) / Redis(生产) | - |
| 部署 | 阿里云函数计算 | - |

---

## 2. 目录结构

### 2.1 前端
```
frontend/
├── adapters/          # 平台适配层
├── components/        # 公共组件
├── mock/              # Mock 数据层
├── pages/             # 页面组件
├── static/            # 静态资源
├── store/             # 全局状态
├── utils/             # 工具函数
├── App.uvue           # 应用入口
├── manifest.json      # 应用配置
└── pages.json         # 路由配置
```

### 2.2 后端
```
backend/
├── routes/            # API 路由
├── services/          # 业务服务
├── utils/             # 工具函数
├── static/legal/      # 法律文档
├── app.py             # 应用工厂
├── config.py          # 配置管理
├── models.py          # 数据模型
├── fc_handler.py      # FC 入口函数
└── s.yaml             # 部署配置
```

---

## 3. 部署架构

```
客户端 (uni-app x)
       │
       ▼ HTTPS
阿里云 API 网关
       │
       ▼ 触发器
阿里云函数计算 (FC)
       │
       ├─► 阿里云 RDS MySQL
       ├─► 阿里云 Redis
       └─► 阿里云 SLS (日志)
```

### 3.1 FC 配置
| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| 内存规格 | 512MB - 1024MB | 根据并发量调整 |
| 执行超时 | 30s | API 响应时间上限 |
| 单实例并发 | 10 | 减少实例创建开销 |
| 预留实例 | 1 | 避免冷启动延迟 |
| VPC 配置 | 与 RDS 同 VPC | 内网访问数据库 |

---

## 4. 核心机制

### 4.1 幂等性保障
- **前端**：为所有非 GET 请求生成唯一 `Idempotency-Key`
- **后端**：使用 `IdempotencyKey` 表记录 24 小时内的请求快照

### 4.2 离线同步
1. 用户提交修改 → 网络不可用 → 存入 localStorage
2. 监听网络状态 → 状态变为 Online → 触发同步
3. 遍历队列重发 → 成功后移除

### 4.3 用户认证
- JWT (HS256) 身份验证，Token 有效期 7 天
- 支持手机号登录、微信登录、Apple 登录

---

## 5. 第三方服务集成

### 5.1 微信开放平台
| 能力 | 接口 | 用途 |
|------|------|------|
| 登录 | code 换取 openid | 用户身份识别 |
| 内容安全 | msgSecCheck | 文本审核 |
| 小程序码 | getwxacodeunlimit | 生成活动二维码 |

### 5.2 阿里云服务
| 服务 | 用途 | 配置项 |
|------|------|--------|
| 短信 | 验证码发送 | ALIYUN_SMS_* |
| Redis | 验证码存储、限流 | REDIS_URL |

---

## 6. 技术规范

### 6.1 网络容错
- 实时监听网络切换，自动重试失败请求
- 无网时顶部显示提示条
- 离线操作存入队列，网络恢复后自动同步

### 6.2 异常处理
- 统一处理 HTTP 401（登录过期跳转登录页）
- 统一处理 HTTP 500/502（服务器故障提示）
- 接入崩溃上报（如 Sentry）

### 6.3 性能优化
- 启动速度：优化首屏渲染时间
- 内存管理：长列表使用虚拟列表
- 包体积：分包加载

---

## 7. 微信小程序集成方案

### 7.1 扫码进入流程
1. App 生成分享二维码
2. 用户微信扫码 → 唤起小程序
3. 小程序解析参数 → 进入活动详情
4. 用户浏览并报名

### 7.2 参数解析
```typescript
onLoad(options) {
  // 扫普通链接二维码 (q参数)
  if (options['q']) {
    const id = decodeURIComponent(options['q']).split('/').pop();
    this.loadActivity(id);
  }
  // 扫小程序码 (scene参数)
  else if (options['scene']) {
    const id = decodeURIComponent(options['scene']).split('=')[1];
    this.loadActivity(id);
  }
  // 内部跳转
  else if (options['id']) {
    this.loadActivity(options['id']);
  }
}
```

### 7.3 账号体系
- 通过手机号作为唯一标识打通 App 和小程序
- 小程序使用微信一键登录获取手机号
- 后端根据手机号匹配或创建用户账号
