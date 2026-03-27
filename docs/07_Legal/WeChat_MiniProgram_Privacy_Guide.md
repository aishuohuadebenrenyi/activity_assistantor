# 微信小程序隐私协议配置指南

> **Version**: v1.0.0 | **Last Updated**: 2026-03-26

本文档详细说明如何在微信公众平台配置小程序隐私协议，确保小程序符合微信平台合规要求。

---

## 一、配置入口

登录 [微信公众平台](https://mp.weixin.qq.com/)，进入小程序管理后台：

```
设置 → 基本设置 → 服务内容声明 → 用户隐私保护指引
```

---

## 二、用户隐私保护指引配置

### 2.1 填写指引内容

在「用户隐私保护指引」页面，填写以下内容：

```
Zentro 活动助手小程序收集以下用户信息：

1. 手机号：用于用户登录验证、活动报名、联系沟通
2. 微信昵称/头像：用于用户信息展示（可选）
3. 位置信息：用于活动地点导航（可选，需用户授权）

我们承诺：
- 仅在实现功能所必需的范围内使用用户信息
- 不向第三方出售用户信息
- 采取合理措施保护用户数据安全
- 用户可申请删除或注销账号

联系方式：【privacy@your-domain.com】
```

### 2.2 配置截图示例

```
┌─────────────────────────────────────────────────────────────┐
│                    用户隐私保护指引                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  指引内容:                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Zentro 活动助手小程序收集以下用户信息：                │   │
│  │                                                      │   │
│  │ 1. 手机号：用于用户登录验证、活动报名、联系沟通        │   │
│  │ 2. 微信昵称/头像：用于用户信息展示（可选）             │   │
│  │ 3. 位置信息：用于活动地点导航（可选，需用户授权）      │   │
│  │                                                      │   │
│  │ 我们承诺：                                            │   │
│  │ - 仅在实现功能所必需的范围内使用用户信息              │   │
│  │ - 不向第三方出售用户信息                              │   │
│  │ - 采取合理措施保护用户数据安全                        │   │
│  │ - 用户可申请删除或注销账号                            │   │
│  │                                                      │   │
│  │ 联系方式：privacy@zentro.app                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                                    [保存] [提交审核]         │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、收集用户信息配置

### 3.1 配置收集的信息类型

在「收集用户信息」页面，勾选以下类型：

| 信息类型 | 是否收集 | 用途说明 |
|----------|----------|----------|
| 手机号 | ✅ 是 | 用于用户登录验证、活动报名、联系沟通 |
| 微信昵称/头像 | ✅ 是 | 用于用户信息展示（可选） |
| 位置信息 | ✅ 是 | 用于活动地点导航（可选，需用户授权） |
| 相册/图片 | ✅ 是 | 用于保存二维码图片到相册 |
| 通讯录 | ❌ 否 | - |
| 日程 | ❌ 否 | - |
| 粘贴板 | ✅ 是 | 用于复制分享链接 |
| 蓝牙 | ❌ 否 | - |
| 运动数据 | ❌ 否 | - |

### 3.2 详细配置说明

#### 手机号

```
收集场景：用户登录、活动报名
使用目的：账号身份验证、报名联系、安全风控
是否必填：是
```

#### 微信昵称/头像

```
收集场景：用户授权获取
使用目的：用户信息展示
是否必填：否
```

#### 位置信息

```
收集场景：活动地点导航
使用目的：显示活动地点、提供导航服务
是否必填：否
```

#### 相册/图片

```
收集场景：保存二维码图片
使用目的：将活动二维码保存到相册
是否必填：否
```

#### 粘贴板

```
收集场景：复制分享链接
使用目的：将分享链接复制到剪贴板
是否必填：否
```

---

## 四、接口使用声明

### 4.1 使用的敏感接口

在「接口使用声明」页面，声明以下接口：

| 接口名称 | 用途说明 | 使用场景 |
|----------|----------|----------|
| wx.login | 用户登录 | 用户打开小程序时进行登录验证 |
| wx.getUserProfile | 获取用户昵称头像 | 用户主动授权获取个人信息 |
| wx.getLocation | 获取位置信息 | 活动地点导航（预留功能） |
| wx.chooseLocation | 选择位置 | 创建活动时选择活动地点（预留） |
| wx.scanCode | 扫码 | 扫描签到二维码进行签到核销 |
| wx.saveImageToPhotosAlbum | 保存图片到相册 | 将活动二维码保存到相册 |
| wx.getClipboardData | 获取剪贴板内容 | 复制分享链接 |
| wx.setClipboardData | 设置剪贴板内容 | 复制分享链接 |

### 4.2 接口配置详情

#### wx.login

```json
{
  "api": "wx.login",
  "usage": "用户登录验证",
  "scene": "用户打开小程序时进行登录验证，获取用户唯一标识"
}
```

#### wx.getUserProfile

```json
{
  "api": "wx.getUserProfile",
  "usage": "获取用户昵称和头像",
  "scene": "用户主动点击授权按钮时获取，用于展示用户信息"
}
```

#### wx.scanCode

```json
{
  "api": "wx.scanCode",
  "usage": "扫描二维码",
  "scene": "主办方扫描参与者签到二维码进行签到核销"
}
```

#### wx.saveImageToPhotosAlbum

```json
{
  "api": "wx.saveImageToPhotosAlbum",
  "usage": "保存图片到相册",
  "scene": "用户点击保存按钮，将活动二维码图片保存到相册"
}
```

---

## 五、隐私协议弹窗配置

### 5.1 小程序端隐私弹窗

微信要求小程序在收集用户信息前进行隐私弹窗授权。需要在 `app.json` 中配置：

```json
{
  "__usePrivacyCheck__": true
}
```

### 5.2 隐私弹窗处理逻辑

在小程序中处理隐私弹窗：

```javascript
// app.js
App({
  onLaunch: function() {
    // 检查隐私协议是否已同意
    wx.getPrivacySetting({
      success: res => {
        if (res.needAuthorization) {
          // 需要弹出隐私协议
          this.globalData.privacyAuthorizationNeed = true
        }
      }
    })
  },
  
  globalData: {
    privacyAuthorizationNeed: false
  }
})
```

### 5.3 隐私协议组件

创建隐私协议弹窗组件：

```html
<!-- components/privacy/privacy.wxml -->
<view class="privacy-mask" wx:if="{{showPrivacy}}">
  <view class="privacy-content">
    <view class="privacy-title">用户隐私保护提示</view>
    <view class="privacy-desc">
      感谢您使用 Zentro 活动助手。为了更好地为您提供服务，我们需要获取以下权限：
      <view class="privacy-list">
        <view>• 手机号：用于登录和活动报名</view>
        <view>• 相机：用于扫码签到</view>
        <view>• 相册：用于保存二维码图片</view>
      </view>
    </view>
    <view class="privacy-buttons">
      <button class="btn-reject" bindtap="handleDisagree">拒绝</button>
      <button class="btn-agree" id="agree-btn" open-type="agreePrivacyAuthorization" bindagreeprivacyauthorization="handleAgree">同意</button>
    </view>
  </view>
</view>
```

```javascript
// components/privacy/privacy.js
Component({
  data: {
    showPrivacy: false
  },
  
  lifetimes: {
    attached() {
      wx.getPrivacySetting({
        success: res => {
          this.setData({
            showPrivacy: res.needAuthorization
          })
        }
      })
    }
  },
  
  methods: {
    handleAgree() {
      this.setData({ showPrivacy: false })
      this.triggerEvent('agree')
    },
    
    handleDisagree() {
      this.setData({ showPrivacy: false })
      this.triggerEvent('disagree')
      wx.showModal({
        title: '提示',
        content: '您拒绝了隐私协议，部分功能可能无法正常使用',
        showCancel: false
      })
    }
  }
})
```

---

## 六、域名配置

### 6.1 服务器域名配置

在「开发管理」→「开发设置」→「服务器域名」中配置：

| 域名类型 | 域名地址 | 用途 |
|----------|----------|------|
| request 合法域名 | https://api.zentro.app | API 请求 |
| uploadFile 合法域名 | https://api.zentro.app | 文件上传 |
| downloadFile 合法域名 | https://api.zentro.app | 文件下载 |

### 6.2 域名配置要求

- 必须使用 HTTPS 协议
- 域名必须经过 ICP 备案
- 域名不能使用 IP 地址
- 域名不能使用端口号

---

## 七、内容安全配置

### 7.1 内容安全接口

Zentro 已接入微信内容安全 API，用于审核用户发布的内容：

| 接口名称 | 用途 | 调用场景 |
|----------|------|----------|
| msgSecCheck | 文本内容审核 | 活动名称、介绍、地点等文本内容 |
| imgSecCheck | 图片内容审核 | 活动封面图片（预留） |

### 7.2 内容安全实现

后端已实现内容安全检测：

```python
# backend/services/wechat_service.py
def check_content_security(self, content: str) -> dict:
    """
    调用微信内容安全 API 检测文本内容
    """
    url = "https://api.weixin.qq.com/wxa/msg_sec_check"
    # ... 实现内容安全检测
```

---

## 八、审核注意事项

### 8.1 审核前检查清单

- [ ] 用户隐私保护指引已填写并提交审核
- [ ] 收集用户信息类型已正确勾选
- [ ] 接口使用声明已完整填写
- [ ] 服务器域名已配置
- [ ] 隐私弹窗功能已实现
- [ ] 内容安全检测已接入

### 8.2 常见审核问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 隐私指引不完整 | 未说明所有收集的信息类型 | 补充完整信息类型和用途 |
| 接口声明缺失 | 使用了未声明的接口 | 在接口声明中添加所有使用的接口 |
| 域名未备案 | 服务器域名未完成 ICP 备案 | 先完成域名 ICP 备案 |
| 内容安全未接入 | 用户发布内容未审核 | 接入微信内容安全 API |

### 8.3 审核被拒处理

如果审核被拒，根据驳回原因进行修改：

1. 登录微信公众平台查看驳回原因
2. 根据原因修改配置或代码
3. 重新提交审核

---

## 九、上线后维护

### 9.1 隐私协议更新

当收集的信息类型或用途发生变化时：

1. 更新用户隐私保护指引内容
2. 更新收集用户信息配置
3. 更新接口使用声明
4. 重新提交审核

### 9.2 定期检查

建议每月检查以下内容：

- [ ] 隐私协议内容是否与实际一致
- [ ] 收集的信息类型是否完整
- [ ] 接口声明是否完整
- [ ] 域名是否有效

---

## 十、相关文档

- [隐私政策](./Privacy_Policy.md)
- [用户协议](./User_Agreement.md)
- [数据收集声明](./Data_Collection_Declaration.md)
- [合规检查清单](../04_Analysis/Compliance_Checklist.md)

---

## 附录：微信官方文档链接

- [小程序用户隐私保护指引填写说明](https://developers.weixin.qq.com/miniprogram/dev/framework/user-privacy/)
- [小程序隐私协议开发指南](https://developers.weixin.qq.com/miniprogram/dev/framework/user-privacy/PrivacyAuthorization.html)
- [内容安全接口文档](https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/sec-check/security.msgSecCheck.html)
- [服务器域名配置](https://developers.weixin.qq.com/miniprogram/dev/framework/ability/network.html)
