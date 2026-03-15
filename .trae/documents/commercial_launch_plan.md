# 独立开发者应用商业化上线计划 (Activity Assistant)

作为一个独立开发者，要将应用打造成成熟的商业产品，除了核心功能外，还需要关注用户体验的稳定性、数据驱动的运营决策以及合规性。以下是针对 Activity Assistant 的商业化上线计划。

## 阶段一：核心体验增强 (Robustness & Offline First) \[Completed ✅]

目标：确保应用在各种网络环境下（弱网、无网）都能稳定运行，不丢失用户数据。

### 1. 全局网络状态管理

* [x] **状态监听**: 在 `App.uvue` 中初始化 `uni.onNetworkStatusChange`，实时监控网络连接状态。

* [x] **全局提示**: 当网络断开时，通过 `uni.showToast` 或状态栏提示。

* [x] **状态共享**: 将网络状态存储在 `utils/network_state.uts` 中，供全局访问。

### 2. 数据持久化与离线支持

* [x] **本地缓存 (Local Storage)**:

  * 核心数据（活动列表、用户信息）均通过 `uni.setStorageSync` 实现持久化。

  * 启动时优先加载缓存，实现秒开。

* [x] **离线操作队列 (Offline Queue)**:

  * 已实现 `utils/offline_queue.uts`。

  * 离线状态下的创建、签到操作自动入队，恢复后自动同步。

### 3. 健壮的错误处理

* [x] **统一请求拦截**:

  * `utils/request.uts` 已集成 401 (过期重定向)、500 (友好提示) 及 Mock 切换逻辑。

* [x] **UI 降级**:

  * 列表空状态、详情不存在状态均已处理。

## 阶段二：数据分析与埋点 (User Behavior Analytics) \[Completed ✅]

目标：了解用户如何使用产品，为产品迭代和商业化决策提供数据支持。

### 1. 隐私优先的埋点系统

* [x] **设计埋点事件表**: 已定义 `page_view`, `activity_create`, `participants_export_submit` 等核心事件。

* [x] **实现埋点服务**: 已封装 `utils/analytics.uts`。

### 2. 用户反馈闭环

* [x] **意见反馈入口**: 已新增 `pages/profile/feedback/feedback.uvue`。

## 阶段三：商业化与合规 (Monetization & Compliance) \[In Progress ⏳]

目标：确保应用符合上架要求并具备盈利潜力。

### 1. 合规性准备

* [x] **注销功能**: 已在“编辑资料”页提供注销账号入口。

* [ ] **隐私政策与用户协议**: 需在登录页补充勾选框及协议内容。

* [ ] **内容安全校验**: 后端已集成微信 SecCheck，前端需进一步完善拦截提示。

### 2. 应用商店优化 (ASO)

* [ ] **截图与预览视频**: 待制作。

## 执行路线图 (Roadmap)

1. **Step 1**: 完成核心体验增强 \[Done]
2. **Step 2**: 完成埋点系统与反馈闭环 \[Done]
3. **Step 3**: 完善合规文档与协议展示 \[Pending]
4. **Step 4**: 提交审核与上线 \[Pending]

