# iOS 合规检查计划：我的页面设置与通知设置

## 一、检查背景

**目标**：检查 Zentro 应用"我的页面"中的显示设置和通知设置是否符合 iOS App Store 规范和 Apple Human Interface Guidelines。

**当前实现文件**：
- 主页面：`/frontend/pages/profile/profile.uvue`
- 关于页面：`/frontend/pages/about/about.uvue`
- 配置文件：`/frontend/manifest.json`
- **新增**：`/frontend/utils/settings.uts`

---

## 二、实施状态

### Phase 1：通知权限合规 ✅ 已完成

| 任务 | 状态 | 说明 |
|------|------|------|
| 1.1 添加通知权限请求 API | ✅ | 创建 `settings.uts` 工具模块 |
| 1.2 实现权限状态检测 | ✅ | `checkNotificationPermission()` 方法 |
| 1.3 添加跳转系统设置功能 | ✅ | `openSystemSettings()` 方法 |
| 1.4 持久化通知偏好设置 | ✅ | `saveNotificationSettings()` / `loadNotificationSettings()` |
| 1.5 更新 UI 显示权限状态 | ✅ | 通知状态显示 + 权限警告提示 |

### Phase 2：显示设置优化 ✅ 已完成

| 任务 | 状态 | 说明 |
|------|------|------|
| 2.1 集成系统主题 API | ✅ | `getSystemTheme()` / `applyTheme()` |
| 2.2 实现主题实时切换 | ✅ | 支持浅色/深色/跟随系统 |
| 2.3 持久化主题设置 | ✅ | `saveThemeSettings()` / `loadThemeSettings()` |

---

## 三、新增功能说明

### 3.1 通知设置改进

**新增功能**：
1. **权限状态检测**：每次打开通知设置时检测系统通知权限状态
2. **权限警告提示**：当系统通知权限未开启时，显示黄色警告条
3. **跳转系统设置**：提供"去设置"按钮，引导用户到系统设置开启权限
4. **通知类型细分**：
   - 主开关：接收实时通知
   - 活动提醒开关
   - 签到提醒开关
5. **设置持久化**：所有通知偏好保存到本地存储

**UI 改进**：
- 通知状态显示颜色：
  - 绿色：已开启
  - 橙色：未授权
  - 灰色：已关闭

### 3.2 显示设置改进

**新增功能**：
1. **系统主题同步**：使用 `uni.getAppBaseInfo()` 获取系统主题
2. **主题应用**：调用 `plus.nativeUI.setUIStyle()` 应用主题
3. **设置持久化**：主题偏好保存到本地存储

---

## 四、代码变更摘要

### 新增文件

| 文件 | 说明 |
|------|------|
| `/frontend/utils/settings.uts` | 设置工具模块，包含通知权限和主题设置相关函数 |

### 修改文件

| 文件 | 变更说明 |
|------|----------|
| `/frontend/pages/profile/profile.uvue` | 集成新的设置功能，改进通知设置 UI |
| `/docs/04_Analysis/Compliance_Checklist.md` | 新增通知权限合规检查项 |

---

## 五、验收标准

### 5.1 通知设置验收 ✅

- [x] 首次使用时检测通知权限状态
- [x] 显示当前系统通知权限状态
- [x] 未授权时提供跳转系统设置的按钮
- [x] 通知偏好设置持久化存储
- [x] 应用重启后设置保持

### 5.2 显示设置验收 ✅

- [x] 主题切换可保存设置
- [x] "跟随系统"选项可用
- [x] 主题设置持久化存储

### 5.3 合规性验收 ✅

- [x] 符合 iOS App Store 审核指南
- [x] 符合 Apple Human Interface Guidelines
- [x] 无语法错误

---

## 六、后续建议（可选）

### Phase 3：用户体验增强

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 创建独立设置页面 | 低 | 将设置从模态框改为独立页面 |
| 添加免打扰时段设置 | 低 | 允许用户设置免打扰时段 |
| 添加通知预览功能 | 低 | 展示通知样式预览 |

---

## 七、结论

**当前合规状态**：✅ 合规

**已完成的改进**：
1. ✅ 通知权限请求流程符合 iOS 规范
2. ✅ 提供跳转系统设置功能
3. ✅ 通知状态与系统权限同步
4. ✅ 设置持久化存储
5. ✅ 主题设置支持系统主题同步

**文件变更**：
- 新增：`/frontend/utils/settings.uts`
- 修改：`/frontend/pages/profile/profile.uvue`
- 更新：`/docs/04_Analysis/Compliance_Checklist.md`
