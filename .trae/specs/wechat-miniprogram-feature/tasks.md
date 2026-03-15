# Tasks

## Phase 1: 基础配置与兼容性 (Basic Setup)
- [x] Task 1.1: 完善 `manifest.json` 配置
  - [x] 设置 `mp-weixin` 的 AppID (如果已有) 或保持测试号。
  - [x] 开启 `lazyCodeLoading` 和 `optimization`。
- [x] Task 1.2: 搭建基础路由与 TabBar (小程序适配)
  - [x] 确保 `pages.json` 中的 TabBar 配置兼容小程序。
  - [x] 处理 App 特有页面在小程序的降级展示。

## Phase 2: 核心业务 - 报名 (Registration)
- [x] Task 2.1: 适配活动详情页 (`detail.uvue`)
  - [x] #ifdef MP-WEIXIN: 隐藏 App 原生导航栏，使用自定义头部或默认头部。
  - [x] #ifdef MP-WEIXIN: 添加 `button open-type="share"` 分享按钮。
  - [x] #ifdef MP-WEIXIN: 底部报名栏逻辑修改 -> 检测未登录弹出授权。
- [x] Task 2.2: 实现微信一键登录 (`auth/login.uvue`)
  - [x] 新增 `uni.login` 获取 code。
  - [x] 新增 `getPhoneNumber` 获取 encryptedData。
  - [x] 对接后端 `/api/auth/wechat` 接口 (需 Mock 或真实对接)。
- [x] Task 2.3: 实现报名逻辑
  - [x] 调用 `/api/activity/:id/join` 接口。
  - [x] 处理重复报名、满员等异常状态。

## Phase 3: 核心业务 - 签到 (Check-in)
- [x] Task 3.1: 开发“我的报名”页 (`user/my-activities.uvue`)
  - [x] 展示已报名活动列表 (进行中/已结束)。
  - [x] 点击卡片进入凭证详情。
- [x] Task 3.2: 开发“报名凭证”页 (`activity/ticket.uvue`)
  - [x] 生成二维码 (使用 `uqrcode` 或类似库)。
  - [x] 内容包含用户 ID 和活动 ID 的加密串。
- [x] Task 3.3: (App端) 开发扫码核销功能
  - [x] 在活动管理页新增“扫一扫”入口。
  - [x] 调用 `uni.scanCode` 识别凭证二维码。
  - [x] 调用 `/api/activity/:id/checkin` 接口完成核销。
- [x] Task 3.4: (小程序端) 开发自助签到功能
  - [x] 在活动详情页/凭证页新增“扫码签到”入口。
  - [x] 识别活动现场二维码 -> 校验 -> 签到成功。

## Phase 4: 验证与发布 (Verification) [Completed ✅]
- [x] Task 4.1: 开发者工具全流程测试 (登录 -> 报名 -> 生成凭证)。
- [x] Task 4.2: 真机扫码测试 (App 扫小程序码)。
