# Zentro 文档中心

> **Version**: v1.0.0 | **Last Updated**: 2026-03-24

## 文档结构

```
docs/
├── 01_Product/
│   └── PRD.md                    # 产品需求文档
├── 02_Technical/
│   ├── Architecture.md           # 技术架构
│   ├── API_Reference.md          # API 接口文档
│   └── Database_Design.md        # 数据库设计
├── 04_Analysis/
│   └── Compliance_Checklist.md   # 合规检查清单
├── 05_User_Support/
│   └── User_Manual.md            # 用户手册
├── 07_Legal/
│   ├── Privacy_Policy.md         # 隐私政策
│   └── User_Agreement.md         # 用户协议
└── README.md                    # 本文档
```

---

## 核心文档

### 产品文档
| 文档 | 说明 |
|------|------|
| [PRD.md](./01_Product/PRD.md) | 产品定位、功能规划、商业化策略 |

### 技术文档
| 文档 | 说明 |
|------|------|
| [Architecture.md](./02_Technical/Architecture.md) | 技术栈、部署架构、核心机制 |
| [API_Reference.md](./02_Technical/API_Reference.md) | 接口定义、错误码规范 |
| [Database_Design.md](./02_Technical/Database_Design.md) | 表结构、索引设计 |

### 合规文档
| 文档 | 说明 |
|------|------|
| [Compliance_Checklist.md](./04_Analysis/Compliance_Checklist.md) | iOS/小程序上架合规要求 |
| [Privacy_Policy.md](./07_Legal/Privacy_Policy.md) | 隐私政策（需填充真实信息） |
| [User_Agreement.md](./07_Legal/User_Agreement.md) | 用户协议（需填充真实信息） |

### 用户支持
| 文档 | 说明 |
|------|------|
| [User_Manual.md](./05_User_Support/User_Manual.md) | 用户使用指南 |

---

## 上线前待办

### 必须完成 (P0)
1. **隐私政策**：填充真实运营主体信息
2. **用户协议**：填充真实运营主体信息
3. **ICP 备案**：完成域名备案
4. **小程序配置**：配置服务器域名、隐私协议

### 后续迭代 (P2)
1. 支付对接（微信支付/Apple 内购）
2. 看板指标写入
3. Android 平台适配

---

## 相关资源

- 项目根目录: `/`
- 前端代码: `/frontend`
- 后端代码: `/backend`
- 部署配置: `/backend/s.yaml`
- 法律文档: `/backend/static/legal/`
