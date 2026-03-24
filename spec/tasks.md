# 上线准备任务清单

> **Version**: v1.0.0 | **Created**: 2026-03-23 | **Updated**: 2026-03-24

## 任务优先级说明
- **P0**: 阻塞性问题，必须解决才能上线
- **P2**: 优化建议，后续迭代解决

---

## 一、阿里云函数计算部署 (P0)

### 1.1 部署验证（需在阿里云控制台操作）
- [ ] **TASK-007**: 部署到 FC 测试环境
  - 执行: `s deploy`
  - 验证: 函数可正常调用

- [ ] **TASK-008**: 配置自定义域名
  - 配置: API 网关 + SSL 证书
  - 验证: HTTPS 访问正常

---

## 二、阿里云基础设施配置 (P0) - 需在控制台操作

### 2.1 RDS MySQL
- [ ] **TASK-009**: 创建 RDS MySQL 实例
- [ ] **TASK-010**: 配置 RDS 白名单
- [ ] **TASK-011**: 配置数据库连接
- [ ] **TASK-012**: 执行数据库迁移

### 2.2 Redis
- [ ] **TASK-013**: 创建 Redis 实例
- [ ] **TASK-014**: 配置 Redis 白名单

### 2.3 VPC 网络
- [ ] **TASK-015**: 创建 VPC 网络
- [ ] **TASK-016**: 配置 FC VPC

### 2.4 日志服务
- [ ] **TASK-017**: 配置 SLS 日志服务

### 2.5 OSS 存储
- [ ] **TASK-018**: 创建 OSS 存储桶
- [ ] **TASK-019**: 配置 CDN 加速

---

## 三、前端配置 (P0)

- [ ] **TASK-020**: 关闭 Mock 模式
  - 文件: `frontend/utils/config.uts`
  - 修改: `USE_MOCK: false`

- [ ] **TASK-021**: 配置生产后端地址
  - 文件: `frontend/utils/config.uts`
  - 修改: `BASE_URL` 为生产环境 HTTPS 地址

- [ ] **TASK-022**: 配置隐私政策 URL
  - 文件: `frontend/utils/config.uts`
  - 修改: `PRIVACY_POLICY_URL` 为生产环境 URL

- [ ] **TASK-023**: 配置用户协议 URL
  - 文件: `frontend/utils/config.uts`
  - 修改: `USER_AGREEMENT_URL` 为生产环境 URL

---

## 四、后端配置 (P0)

- [ ] **TASK-024**: 配置生产密钥
  - 环境变量: `SECRET_KEY`
  - 说明: 替换默认值 `dev-secret-key-change-in-prod`

- [ ] **TASK-025**: 配置微信小程序凭证
  - 环境变量: `WECHAT_APPID`, `WECHAT_SECRET`
  - 说明: 替换 Mock 值 `wx1234567890abcdef`

---

## 五、法律合规 (P0)

- [ ] **TASK-029**: 完善隐私政策内容
  - 文件: `backend/static/legal/privacy.html`
  - 内容: 填写运营主体、联系邮箱、生效日期

- [ ] **TASK-030**: 完善用户协议内容
  - 文件: `backend/static/legal/terms.html`
  - 内容: 填写运营主体、联系邮箱、生效日期

- [ ] **TASK-031**: 更新后端静态法律页面
  - 验证: 页面可正常访问

---

## 六、iOS App Store (P0)

- [ ] **TASK-032**: 准备 App 图标
  - 尺寸: 1024×1024, 180×180, 120×120, 167×167, 152×152, 76×76
  - 参考: `spec/assets-checklist.md`

- [ ] **TASK-033**: 准备启动页
  - 尺寸: iPhone 各机型竖屏尺寸
  - 参考: `spec/assets-checklist.md`

- [ ] **TASK-034**: 准备应用截图
  - 数量: 每种设备 2-10 张
  - 参考: `spec/assets-checklist.md`

- [ ] **TASK-037**: 注册 Apple 开发者账号
  - 费用: $99/年

- [ ] **TASK-038**: 创建 App ID
  - Bundle ID: 需替换 `com.yourcompany.activityassistant`

- [ ] **TASK-039**: 配置 App Store Connect 信息
  - 内容: 应用名称、描述、关键词、截图等

---

## 七、微信小程序 (P0)

- [ ] **TASK-040**: 注册微信小程序账号
  - 平台: https://mp.weixin.qq.com

- [ ] **TASK-041**: 配置小程序类目
  - 建议: 工具 > 效率

- [ ] **TASK-042**: 配置服务器域名
  - 域名: 生产环境 API 域名

- [ ] **TASK-043**: 配置业务域名
  - 域名: 用于 Webview 加载

- [ ] **TASK-044**: 配置隐私协议
  - 内容: 用户隐私保护指引

---

## 八、后续迭代版本 (P2)

### 8.1 商业化功能
- [ ] **P2-001**: 支付对接
  - 文件: `backend/routes/billing.py`
  - 说明: 对接微信支付/Apple 内购

### 8.2 数据分析
- [ ] **P2-002**: 看板指标写入
  - 文件: `backend/routes/analytics.py:119`
  - 说明: 实现指标聚合写入逻辑

### 8.3 平台适配
- [ ] **P2-003**: Android 平台适配
  - 文件: `frontend/adapters/platform.uts:32`
  - 说明: 完善 Android 平台适配

### 8.4 第三方服务
- [ ] **P2-004**: 腾讯地图 Key 配置
  - 文件: `frontend/pages/activity/ticket/ticket.uvue:192`
  - 说明: 替换 `YOUR_TENCENT_MAP_KEY` 为真实 Key

---

## 任务统计

| 类别 | 待完成 | 说明 |
|------|--------|------|
| FC 部署验证 | 2 | 需在阿里云控制台操作 |
| 基础设施配置 | 11 | 需在阿里云控制台操作 |
| 前端配置 | 4 | 关闭 Mock、配置地址 |
| 后端配置 | 2 | 密钥、微信凭证 |
| 法律合规 | 3 | 隐私政策、用户协议 |
| iOS App Store | 6 | 应用素材、开发者账号 |
| 微信小程序 | 5 | 账号注册、域名配置 |
| 后续迭代 P2 | 4 | 支付、指标、适配、地图 |
| **总计** | **37** | |
