# App 和小程序图标素材清单

本文档列出 Zentro 应用在各平台发布所需的图标和素材。

---

## 一、微信小程序图标

### 1. 小程序头像/Logo（后台配置）

| 用途 | 尺寸 | 格式 | 大小限制 | 说明 |
|------|------|------|----------|------|
| 小程序头像 | **144×144 px** | PNG（推荐） | ≤ 2M | 上传后自动切割成圆形，注意安全边距 |

### 2. TabBar 底部导航图标

| 用途 | 尺寸 | 格式 | 大小限制 |
|------|------|------|----------|
| TabBar 图标 | **81×81 px** | PNG | ≤ 30KB |

**项目需要的 TabBar 图标**（每个需要普通态和选中态）：

```
frontend/static/tabbar/
├── home.png          # 首页-普通
├── home-active.png   # 首页-选中
├── add.png           # 创建-普通
├── add-active.png    # 创建-选中
├── ticket.png        # 票券-普通
├── ticket-active.png # 票券-选中
├── profile.png       # 我的-普通
└── profile-active.png # 我的-选中
```

### 3. 分享图标

| 用途 | 尺寸 | 格式 | 说明 |
|------|------|------|------|
| 分享给好友/朋友圈 | **500×500 px** | PNG/JPG | 比例严格 1:1 |

---

## 二、iOS App 图标

### 1. App 图标（必需）

| 用途 | 尺寸 | 说明 |
|------|------|------|
| App Store | **1024×1024 px** | 上架必需，无圆角无透明 |
| iPhone @3x | **180×180 px** | iPhone 6 Plus 及以上 |
| iPhone @2x | **120×120 px** | iPhone 4/5/6/7/8 |
| iPad Pro 12.9" | **167×167 px** | iPad Pro 大屏 |
| iPad Pro 11"/10.5" | **152×152 px** | iPad Pro 中屏 |
| iPad @2x | **76×76 px** | iPad 普通屏 |
| Spotlight 搜索 | **120×120 px** | iOS 搜索结果 |
| Settings 设置 | **58×58 px** | 系统设置中显示 |

### 2. 启动图（Launch Screen）

| 设备 | 尺寸 |
|------|------|
| iPhone 14 Pro Max | 1290×2796 px |
| iPhone 14 Pro | 1179×2556 px |
| iPhone 14 | 1170×2532 px |
| iPhone SE (3rd) | 750×1334 px |
| iPad Pro 12.9" | 2048×2732 px |
| iPad Pro 11" | 1668×2388 px |

### 3. App Store 截图（上架必需）

| 设备类型 | 尺寸 | 数量 |
|----------|------|------|
| 6.7" (iPhone 14 Pro Max) | 1290×2796 px | 2-10 张 |
| 6.5" (iPhone 11 Pro Max) | 1242×2688 px | 2-10 张 |
| 5.5" (iPhone 8 Plus) | 1242×2208 px | 2-10 张 |
| 12.9" iPad Pro | 2048×2732 px | 2-10 张 |

---

## 三、Android App 图标

### 1. App 图标（必需）

| 密度 | 尺寸 | 说明 |
|------|------|------|
| **xxxhdpi** | **192×192 px** | 超高清屏 |
| **xxhdpi** | **144×144 px** | 高清屏（主流） |
| **xhdpi** | **96×96 px** | 中高清屏 |
| **hdpi** | **72×72 px** | 高密度屏 |
| mdpi | **48×48 px** | 标准屏 |

### 2. 启动图（Splash Screen）

| 密度 | 尺寸 |
|------|------|
| xxxhdpi | 1280×1920 px |
| xxhdpi | 1080×1920 px |
| xhdpi | 720×1280 px |
| hdpi | 480×800 px |

### 3. 应用商店截图

| 用途 | 尺寸 |
|------|------|
| 手机截图 | 1080×1920 px 或 1080×2340 px |
| 平板截图 | 2560×1600 px |

---

## 四、素材清单汇总

### 必须准备的素材

| 类别 | 素材 | 数量 | 状态 |
|------|------|------|------|
| **微信小程序** | 小程序头像 | 1 张 | ⬜ 待准备 |
| | TabBar 图标（普通+选中） | 8 张 | ⬜ 待准备 |
| | 分享图标 | 1 张 | ⬜ 待准备 |
| **iOS App** | App Store 图标 (1024px) | 1 张 | ⬜ 待准备 |
| | 各尺寸图标 | 6-8 张 | ⬜ 待准备 |
| | 启动图 | 3-5 张 | ⬜ 待准备 |
| | App Store 截图 | 6-30 张 | ⬜ 待准备 |
| **Android App** | 各密度图标 | 5 张 | ⬜ 待准备 |
| | 启动图 | 3-4 张 | ⬜ 待准备 |
| | 应用商店截图 | 3-5 张 | ⬜ 待准备 |

---

## 五、设计建议

### 1. 图标设计原则

- 主图标保持简洁，避免过多细节
- 注意圆角裁剪的安全边距（内容不要太靠边）
- iOS 图标无圆角无透明通道
- Android 支持 Adaptive Icon（前景+背景分离）

### 2. TabBar 图标规范

- 尺寸：81×81 px
- 格式：PNG（支持透明）
- 普通态：灰色（#8E8E93）
- 选中态：主题色（#007AFF）

### 3. 推荐工具

| 工具 | 用途 | 链接 |
|------|------|------|
| App Icon Generator | 图标批量生成 | https://appicon.co/ |
| Squoosh | 图片压缩 | https://squoosh.app/ |
| Figma | UI 设计 | https://www.figma.com/ |
| Sketch | UI 设计 | https://www.sketch.com/ |

---

## 六、manifest.json 配置路径

素材准备好后，需要在以下配置文件中设置路径：

### iOS 配置位置

```json
// frontend/manifest.json -> app-ios.distribute
{
  "icons": {
    "appstore": "static/icons/ios/appstore-1024.png",
    "iphone": {
      "app@2x": "static/icons/ios/iphone-120.png",
      "app@3x": "static/icons/ios/iphone-180.png"
    },
    "ipad": {
      "app": "static/icons/ios/ipad-76.png",
      "app@2x": "static/icons/ios/ipad-152.png",
      "proapp@2x": "static/icons/ios/ipad-167.png"
    }
  },
  "splashScreens": {
    "iphone": {
      "portrait": "static/splash/ios/iphone-portrait.png"
    }
  }
}
```

### Android 配置位置

```json
// frontend/manifest.json -> app-android.distribute
{
  "icons": {
    "hdpi": "static/icons/android/hdpi-72.png",
    "xhdpi": "static/icons/android/xhdpi-96.png",
    "xxhdpi": "static/icons/android/xxhdpi-144.png",
    "xxxhdpi": "static/icons/android/xxxhdpi-192.png"
  },
  "splashScreens": {
    "default": {
      "xxxhdpi": "static/splash/android/xxxhdpi.png"
    }
  }
}
```

---

## 七、素材存放目录结构

```
frontend/static/
├── icons/
│   ├── ios/
│   │   ├── appstore-1024.png
│   │   ├── iphone-120.png
│   │   ├── iphone-180.png
│   │   ├── ipad-76.png
│   │   ├── ipad-152.png
│   │   └── ipad-167.png
│   └── android/
│       ├── hdpi-72.png
│       ├── xhdpi-96.png
│       ├── xxhdpi-144.png
│       └── xxxhdpi-192.png
├── splash/
│   ├── ios/
│   │   └── iphone-portrait.png
│   └── android/
│       └── xxxhdpi.png
├── tabbar/
│   ├── home.png
│   ├── home-active.png
│   ├── add.png
│   ├── add-active.png
│   ├── ticket.png
│   ├── ticket-active.png
│   ├── profile.png
│   └── profile-active.png
└── screenshots/
    ├── ios/
    │   ├── iphone-67-1.png
    │   ├── iphone-67-2.png
    │   └── ...
    └── android/
        ├── phone-1.png
        ├── phone-2.png
        └── ...
```
