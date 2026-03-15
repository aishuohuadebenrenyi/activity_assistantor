# 按钮视觉规范统一改造报告

## 目标

- 使用项目既定按钮基础类（`.btn` / `.btn-text`）统一跨页面按钮视觉
- 将目标按钮统一到与首页“新建”按钮一致的视觉风格（尺寸/圆角/字号/配色/动效）
- 清理各页面内对按钮的冗余样式，避免跨页面视觉漂移

## 设计 Token 与类映射

### 全局 Token（CSS 变量）

来源：[App.uvue](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/App.uvue)

- 颜色：`--primary`、`--primary-strong`、`--text-*`、`--separator` 等
- 圆角：`--radius-*`、`--radius-circle`
- 间距：`--spacing-*`
- 可访问性：`--focus-ring`

### 全局按钮基础类

来源：[App.uvue](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/App.uvue)

- 基类：`.btn`、`.btn-text`
- 尺寸/布局：`.btn-sm`、`.btn-row`
- 文本/图标：`.btn-text-sm`、`.btn-icon-sm`
- 交互反馈：`.hover-opacity`、`.btn:hover`、`.btn:active`、`.btn:focus`、`.btn:focus-visible`

## 改造范围与结果

### 个人主页：编辑入口按钮

文件：[profile.uvue](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/pages/profile/profile.uvue)

- 将编辑入口改为与首页“新建”一致的按钮外观：`class="btn btn-primary btn-sm btn-row"` + `aria-label`
- 移除旧的局部按钮样式（`edit-entry*`）

### 活动详情页：编辑按钮与保存按钮

文件：[detail.uvue](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/pages/activity/detail/detail.uvue)

- 头部“编辑/完成”与首页“新建”一致：`class="btn btn-primary btn-sm btn-row"` + `:aria-label`
- “保存修改”与首页“新建”一致：`class="btn btn-primary btn-sm"`
- 移除旧的 `header-action/action-text` 冗余样式

### 报名人员管理页：扫码按钮与导出按钮

文件：[participants.uvue](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/pages/activity/participants/participants.uvue)

- 将“扫码/导出”与首页“新建”一致：`class="btn btn-primary btn-sm btn-row"` + `aria-label`
- 移除旧的 `header-action/action-text` 冗余样式，使用 `.header-actions` 进行布局

### 首页：新建按钮

文件：[activities.uvue](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/pages/activities/activities.uvue)

- 将原页面内样式（`primary-btn-small/icon-plus-small/btn-text-small`）替换为全局按钮基类组合，作为统一视觉基准：`class="btn btn-primary btn-sm btn-row"`

## 可访问性验证点

- 交互状态：`.btn:hover`、`.btn:active`、`.btn-disabled/.btn[disabled]` 覆盖默认/悬停/点击/禁用
- 语义与读屏：为关键按钮补充 `aria-label`
- 键盘焦点：全局 `.btn:focus/:focus-visible` 提供明显焦点环

## UI 走查清单（人工验证）

- iOS/Android：头部图标按钮点击命中准确；无多余点击热区；按钮按下/悬停反馈一致
- H5：Chrome/Safari/Edge 下
  - Tab 可聚焦到按钮（按钮元素默认可聚焦）
  - 焦点环显示正常
  - 纯图标按钮读屏名称可读（检查 aria-label）

## 视觉对比测试（与首页“新建”一致性）

基准按钮：首页活动列表卡片头部的“新建”（[activities.uvue](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/pages/activities/activities.uvue)）。

需对比的目标按钮：

- 个人主页：用户卡片右侧“编辑”（[profile.uvue](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/pages/profile/profile.uvue)）
- 活动详情页：详细信息卡片头部“编辑/完成”、编辑态“保存修改”（[detail.uvue](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/pages/activity/detail/detail.uvue)）
- 报名人员页：报名人员卡片头部“扫码/导出”（[participants.uvue](file:///Users/leehuyoo/Documents/project/activity_assistant/activity_assistant_v6/frontend/pages/activity/participants/participants.uvue)）

对比维度（每个按钮都需要逐项一致）：

- 默认态：背景色、文字色、字体（字号/字重/字体族）、高度、内边距、圆角、阴影
- 悬停态（H5）：opacity/背景变化、过渡时长与缓动
- 点击态：opacity/缩放、过渡时长与缓动
- 禁用态：透明度与交互不可用（如存在禁用按钮的场景）
- 响应式：小屏/大屏下不挤压、不重叠、对齐一致

## 视觉对比截图（待补充）

建议按页面分别截图“改造前/改造后”，并固定同一机型与同一缩放比：

- 个人主页：用户卡片右侧编辑入口
- 活动详情页：详细信息卡片头部编辑入口 + 编辑态“保存修改”
- 报名人员页：报名人员卡片头部扫码/导出入口
