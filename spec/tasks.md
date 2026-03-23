# 上线准备任务清单

> **Version**: v1.2.0 | **Created**: 2026-03-23 | **Updated**: 2026-03-23

## 任务优先级说明
- **P0**: 阻塞性问题，必须解决才能上线
- **P1**: 重要问题，强烈建议解决（后续迭代）
- **P2**: 优化建议，建议解决（后续迭代）

---

## 一、代码层面 P0 任务（初次上线必须）

### 1.1 后端 - 短信服务集成
- [x] **CODE-001**: 集成阿里云短信 SDK
  - 文件: `backend/services/sms_service.py`
  - 内容: 支持生产/开发双模式，配置环境变量后自动切换
  - 验证: 配置凭证后可发送真实短信

### 1.2 后端 - 验证码存储迁移
- [x] **CODE-002**: 迁移验证码存储到 Redis
  - 文件: `backend/routes/auth.py`
  - 内容: 支持 Redis/内存双模式，配置 REDIS_URL 后自动切换
  - 验证: 多进程验证码一致

### 1.3 前端 - 账号注销功能
- [x] **CODE-003**: 实现前端账号注销接口调用
  - 文件: `frontend/pages/profile/edit/edit.uvue`
  - 内容: 调用后端注销 API，处理冷静期响应
  - 验证: 注销流程完整可用

---

## 二、阿里云函数计算部署 (P0)

### 2.1 FC 入口适配
- [x] **TASK-001**: 创建 FC 入口函数
  - 文件: `backend/fc_handler.py`
  - 验证: 入口函数已创建

- [x] **TASK-002**: 创建 Serverless Devs 部署配置
  - 文件: `backend/s.yaml`
  - 验证: 配置文件已创建

- [x] **TASK-003**: 添加健康检查接口
  - 文件: `backend/app.py`
  - 验证: `/health` 接口已添加

### 2.2 限流存储迁移
- [x] **TASK-004**: 迁移限流存储到 Redis
  - 文件: `backend/app.py`
  - 验证: 支持 Redis 存储

- [x] **TASK-005**: 配置 Redis 连接
  - 文件: `backend/config.py`
  - 验证: REDIS_URL 环境变量已支持

### 2.3 数据库连接优化
- [x] **TASK-006**: 优化数据库连接池
  - 文件: `backend/config.py`
  - 验证: 连接池参数已配置

### 2.4 部署验证（需在阿里云控制台操作）
- [ ] **TASK-007**: 部署到 FC 测试环境
  - 执行: `s deploy`
  - 验证: 函数可正常调用

- [ ] **TASK-008**: 配置自定义域名
  - 配置: API 网关 + SSL 证书
  - 验证: HTTPS 访问正常

---

## 三、阿里云基础设施配置 (P0) - 需在控制台操作

### 3.1 RDS MySQL
- [ ] **TASK-009**: 创建 RDS MySQL 实例
- [ ] **TASK-010**: 配置 RDS 白名单
- [ ] **TASK-011**: 配置数据库连接
- [ ] **TASK-012**: 执行数据库迁移

### 3.2 Redis
- [ ] **TASK-013**: 创建 Redis 实例
- [ ] **TASK-014**: 配置 Redis 白名单

### 3.3 VPC 网络
- [ ] **TASK-015**: 创建 VPC 网络
- [ ] **TASK-016**: 配置 FC VPC

### 3.4 日志服务
- [ ] **TASK-017**: 配置 SLS 日志服务

### 3.5 OSS 存储
- [ ] **TASK-018**: 创建 OSS 存储桶
- [ ] **TASK-019**: 配置 CDN 加速

---

## 四、前端配置 (P0)

- [ ] **TASK-020**: 关闭 Mock 模式
- [ ] **TASK-021**: 配置生产后端地址
- [ ] **TASK-022**: 配置隐私政策 URL
- [ ] **TASK-023**: 配置用户协议 URL

---

## 五、后端配置 (P0)

- [ ] **TASK-024**: 配置生产密钥
- [ ] **TASK-025**: 配置微信小程序凭证

---

## 六、法律合规 (P0)

- [ ] **TASK-029**: 完善隐私政策内容
- [ ] **TASK-030**: 完善用户协议内容
- [ ] **TASK-031**: 更新后端静态法律页面

---

## 七、iOS App Store (P0)

- [ ] **TASK-032**: 准备 App 图标
- [ ] **TASK-033**: 准备启动页
- [ ] **TASK-034**: 准备应用截图
- [x] **TASK-036**: 实现 Apple 登录后端验证
  - 文件: `backend/routes/auth.py`
  - 说明: 实现 `/auth/login/apple` 接口，验证 Apple Identity Token
- [ ] **TASK-037**: 注册 Apple 开发者账号
- [ ] **TASK-038**: 创建 App ID
- [ ] **TASK-039**: 配置 App Store Connect 信息

---

## 八、微信小程序 (P0)

- [ ] **TASK-040**: 注册微信小程序账号
- [ ] **TASK-041**: 配置小程序类目
- [ ] **TASK-042**: 配置服务器域名
- [ ] **TASK-043**: 配置业务域名
- [ ] **TASK-044**: 配置隐私协议

---

## 九、后续迭代版本 (P1)

以下功能已完成实现：

### 9.1 后端功能
- [x] **P1-001**: 举报功能落库
  - 文件: `backend/routes/user.py`
  - 说明: 实现举报记录存储和后台处理流程

- [x] **P1-002**: 邮件导出功能
  - 文件: `backend/services/email_service.py`, `backend/routes/participant.py`
  - 说明: 集成邮件发送服务，支持 Mock/生产双模式

### 9.2 前端功能
- [x] **P1-003**: 海报保存功能
  - 文件: `frontend/pages/activity/share/share.uvue`
  - 说明: 实现 Base64 图片保存到相册

- [x] **P1-004**: 地图导航功能
  - 文件: `frontend/pages/activity/ticket/ticket.uvue`
  - 说明: 调用 uni.openLocation() 实现真实地图导航

- [x] **P1-005**: 取消签到功能
  - 文件: `frontend/pages/activity/participants/participants.uvue`, `backend/routes/participant.py`
  - 说明: 实现取消签到逻辑

---

## 十、后续迭代版本 (P2)

### 10.1 商业化功能
- [ ] **P2-001**: 支付对接
  - 文件: `backend/routes/billing.py`
  - 说明: 对接微信支付/Apple 内购

### 10.2 数据分析
- [ ] **P2-002**: 看板指标写入
  - 文件: `backend/routes/analytics.py:119`
  - 说明: 实现指标聚合写入逻辑

### 10.3 平台适配
- [ ] **P2-003**: Android 平台适配
  - 文件: `frontend/adapters/platform.uts:32`
  - 说明: 完善 Android 平台适配

---

## 任务统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 代码层面 P0 (已完成) | 3 | 短信服务、验证码存储、账号注销 |
| FC 部署 (已完成) | 6 | 入口函数、配置、健康检查、限流、Redis、连接池 |
| 基础设施配置 | 11 | 需在阿里云控制台操作 |
| 前端配置 | 4 | 关闭 Mock、配置地址 |
| 后端配置 | 2 | 密钥、微信凭证 |
| 法律合规 | 3 | 隐私政策、用户协议 |
| iOS App Store | 7 | 应用素材、开发者账号 |
| 微信小程序 | 5 | 账号注册、域名配置 |
| 后续迭代 P1 | 5 | 举报、邮件、海报、导航、签到 |
| 后续迭代 P2 | 3 | 支付、指标、适配 |
