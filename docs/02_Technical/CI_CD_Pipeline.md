# CI/CD 部署流程文档

> 版本：1.0  
> 更新日期：2026-03-26  
> 适用范围：Zentro 活动助手后端服务

---

## 一、CI/CD 架构概览

### 1.1 流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CI/CD Pipeline                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  代码提交                                                                   │
│  ┌───────┐                                                                  │
│  │  Git  │                                                                  │
│  │ Push  │                                                                  │
│  └───┬───┘                                                                  │
│      │                                                                      │
│      ▼                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        GitHub Actions                                  │ │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐ │ │
│  │  │  Lint   │──▶│  Test   │──▶│Security │──▶│  Build  │──▶│ Deploy  │ │ │
│  │  │  检查   │   │  测试   │   │  扫描   │   │  镜像   │   │  部署   │ │ │
│  │  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│      │                                                                      │
│      ▼                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        阿里云基础设施                                   │ │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                  │ │
│  │  │   ACR       │   │    FC       │   │    OSS      │                  │ │
│  │  │  容器镜像   │   │  函数计算   │   │  对象存储   │                  │ │
│  │  └─────────────┘   └─────────────┘   └─────────────┘                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 环境划分

| 环境 | 分支 | 域名 | 用途 |
|------|------|------|------|
| Development | develop | dev-api.zentro.app | 开发测试 |
| Staging | release/* | staging-api.zentro.app | 预发布验证 |
| Production | main | api.zentro.app | 生产环境 |

---

## 二、GitHub Secrets 配置

### 2.1 必需的 Secrets

```yaml
# 阿里云账号配置
ALIYUN_ACCOUNT_ID: "阿里云账号ID"
ALIYUN_ACCESS_KEY_ID: "阿里云AccessKey ID"
ALIYUN_ACCESS_KEY_SECRET: "阿里云AccessKey Secret"

# 容器镜像服务配置
ALIYUN_REGISTRY: "registry.cn-hangzhou.aliyuncs.com/zentro"
ALIYUN_REGISTRY_USERNAME: "容器镜像服务用户名"
ALIYUN_REGISTRY_PASSWORD: "容器镜像服务密码"

# 数据库配置
DATABASE_URL: "mysql://user:password@host:port/database"
REDIS_URL: "redis://host:6379/0"

# 微信配置
WECHAT_APPID: "微信小程序AppID"
WECHAT_SECRET: "微信小程序Secret"

# 安全配置
SECRET_KEY: "Flask应用密钥"
ENCRYPTION_KEY: "备份加密密钥"

# 通知配置
SLACK_WEBHOOK_URL: "Slack Webhook URL"
```

### 2.2 配置方法

1. 进入 GitHub 仓库
2. Settings → Secrets and variables → Actions
3. 点击 "New repository secret"
4. 输入 Name 和 Value
5. 点击 "Add secret"

---

## 三、阿里云函数计算配置

### 3.1 s.yaml 配置详解

```yaml
edition: 1.0.0
name: activity-assistant
access: default

vars:
  region: cn-hangzhou
  serviceName: activity-assistant-api
  functionName: flask-api

services:
  activity-assistant:
    component: fc
    props:
      region: ${vars.region}
      service:
        name: ${vars.serviceName}
        description: Zentro 活动帮手后端服务
        internetAccess: true
        logConfig: auto
        vpcConfig:
          vpcId: ${env.VPC_ID}
          vswitchIds:
            - ${env.VSWITCH_ID}
        nasConfig: auto
      function:
        name: ${vars.functionName}
        description: Flask API 函数
        runtime: python3.9
        codeUri: ./
        handler: fc_handler.handler
        memorySize: 512
        timeout: 30
        instanceConcurrency: 10
        instanceType: e1
        environmentVariables:
          SECRET_KEY: ${env.SECRET_KEY}
          DATABASE_URL: ${env.DATABASE_URL}
          REDIS_URL: ${env.REDIS_URL}
          WECHAT_APPID: ${env.WECHAT_APPID}
          WECHAT_SECRET: ${env.WECHAT_SECRET}
          FC_SERVICE_NAME: ${vars.serviceName}
          LOG_FORMAT: json
          LOG_LEVEL: INFO
      triggers:
        - name: httpTrigger
          type: http
          config:
            authType: anonymous
            methods:
              - GET
              - POST
              - PUT
              - DELETE
              - PATCH
              - HEAD
              - OPTIONS
      customDomains:
        - domainName: ${env.API_DOMAIN}
          protocol: HTTP,HTTPS
          certConfig:
            certName: ${env.SSL_CERT_NAME}
            certificate: ${env.SSL_CERT}
            privateKey: ${env.SSL_KEY}
          routeConfigs:
            - path: /*
              serviceName: ${vars.serviceName}
              functionName: ${vars.functionName}
```

### 3.2 fc_handler.py

```python
"""
阿里云函数计算入口处理器

该模块提供函数计算的入口点，将FC事件转换为Flask请求。
"""

import json
from flask import Request
from backend.app import create_app

app = create_app()

def handler(event, context):
    """
    函数计算入口函数
    
    Args:
        event: FC事件对象，包含HTTP请求信息
        context: FC上下文对象，包含运行时信息
    
    Returns:
        dict: HTTP响应
    """
    # 解析事件
    if isinstance(event, str):
        event = json.loads(event)
    
    # 构建Flask请求环境
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    headers = event.get('headers', {})
    query_string = event.get('queryParameters', {})
    body = event.get('body', '')
    
    # 创建Flask请求
    with app.test_client() as client:
        response = client.open(
            path=path,
            method=method,
            headers=headers,
            query_string=query_string,
            data=body if body else None,
            content_type=headers.get('Content-Type', 'application/json')
        )
    
    # 返回FC响应格式
    return {
        'statusCode': response.status_code,
        'headers': dict(response.headers),
        'body': response.get_data(as_text=True)
    }
```

---

## 四、部署流程

### 4.1 自动部署触发条件

| 触发事件 | 目标环境 | 条件 |
|----------|----------|------|
| Push to `develop` | Development | 自动 |
| Push to `release/*` | Staging | 自动 |
| Push to `main` | Production | 自动 |
| Pull Request | - | 仅运行测试 |
| Manual Dispatch | 指定环境 | 手动触发 |

### 4.2 部署步骤详解

```
┌─────────────────────────────────────────────────────────────────┐
│                        部署流程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: 代码检查 (Lint)                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Flake8 语法检查                                        │   │
│  │ • Black 代码格式检查                                      │   │
│  │ • isort 导入排序检查                                      │   │
│  │ • 失败则终止流程                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Step 2: 单元测试 (Test)                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • 运行 pytest 测试套件                                    │   │
│  │ • 生成覆盖率报告                                          │   │
│  │ • 覆盖率低于60%则失败                                     │   │
│  │ • 上传报告到 Codecov                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Step 3: 安全扫描 (Security)                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Bandit 安全漏洞扫描                                     │   │
│  │ • Safety 依赖漏洞检查                                     │   │
│  │ • 生成安全报告                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Step 4: 构建镜像 (Build)                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • 构建Docker镜像                                          │   │
│  │ • 推送到阿里云容器镜像服务                                 │   │
│  │ • 生成镜像标签（SHA、分支名、latest）                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Step 5: 部署服务 (Deploy)                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • 使用 Serverless Devs 部署到函数计算                     │   │
│  │ • 执行健康检查                                            │   │
│  │ • 发送部署通知                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 手动部署

```bash
# 安装 Serverless Devs
npm install -g @serverless-devs/s

# 配置阿里云凭证
s config add

# 部署到开发环境
s deploy --stage dev

# 部署到生产环境
s deploy --stage prod

# 查看部署状态
s info

# 查看日志
s logs
```

---

## 五、回滚策略

### 5.1 自动回滚条件

- 健康检查连续失败3次
- 错误率超过阈值（>5%）
- 响应时间异常（>5s）

### 5.2 手动回滚

```bash
# 查看版本历史
s version list

# 回滚到指定版本
s version rollback --version-id <version-id>

# 或通过 GitHub Actions
# 在 Actions 页面选择 "Rollback" workflow
# 输入要回滚的版本ID
```

### 5.3 回滚流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        回滚流程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 发现问题                                                    │
│     └── 监控告警 / 用户反馈 / 自动检测                          │
│                                                                 │
│  2. 评估影响                                                    │
│     └── 确认问题范围和严重程度                                  │
│                                                                 │
│  3. 决定回滚                                                    │
│     └── 问题严重且无法快速修复                                  │
│                                                                 │
│  4. 执行回滚                                                    │
│     ├── 方式一：GitHub Actions 手动触发                         │
│     └── 方式二：命令行 s version rollback                       │
│                                                                 │
│  5. 验证恢复                                                    │
│     └── 健康检查、功能测试                                      │
│                                                                 │
│  6. 问题分析                                                    │
│     └── 定位根因、修复代码、更新测试                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 六、监控与告警

### 6.1 监控指标

| 指标 | 阈值 | 告警级别 |
|------|------|----------|
| 函数执行时间 | > 5s | WARNING |
| 函数内存使用 | > 80% | WARNING |
| 函数错误率 | > 1% | WARNING |
| 函数错误率 | > 5% | CRITICAL |
| 冷启动次数 | > 100/min | WARNING |
| 并发实例数 | > 50 | WARNING |

### 6.2 日志收集

```yaml
# 阿里云日志服务配置
logConfig:
  project: zentro-logs
  logstore: api-logs
  enableRequestMetrics: true
  enableInstanceMetrics: true
```

### 6.3 告警配置

```json
{
  "alerts": [
    {
      "name": "high_error_rate",
      "condition": "error_rate > 0.05",
      "severity": "critical",
      "actions": ["email", "sms", "slack"]
    },
    {
      "name": "slow_response",
      "condition": "p99_latency > 3000",
      "severity": "warning",
      "actions": ["email", "slack"]
    }
  ]
}
```

---

## 七、安全配置

### 7.1 网络安全

```yaml
# VPC配置
vpcConfig:
  vpcId: vpc-xxx
  vswitchIds:
    - vsw-xxx
  securityGroupId: sg-xxx

# 访问控制
accessControl:
  whitelist:
    - 10.0.0.0/8
  blacklist: []
```

### 7.2 密钥管理

```
┌─────────────────────────────────────────────────────────────────┐
│                        密钥管理策略                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  存储位置：                                                     │
│  ├── GitHub Secrets: CI/CD流程使用                              │
│  ├── 阿里云KMS: 运行时敏感配置                                  │
│  └── 环境变量: 非敏感配置                                       │
│                                                                 │
│  轮换策略：                                                     │
│  ├── 数据库密码: 每90天                                         │
│  ├── API密钥: 每180天                                           │
│  └── JWT密钥: 每年                                              │
│                                                                 │
│  访问控制：                                                     │
│  ├── 最小权限原则                                               │
│  ├── 审计日志记录                                               │
│  └── 多因素认证                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 八、常见问题

### 8.1 部署失败排查

```bash
# 查看函数日志
s logs --tail

# 查看函数详情
s info

# 本地调试
s local start

# 检查配置
s config get
```

### 8.2 性能优化

- 调整内存配置（影响CPU性能）
- 配置预留实例（减少冷启动）
- 启用实例生命周期回调
- 优化代码依赖大小

### 8.3 成本优化

- 合理设置实例并发数
- 配置弹性伸缩规则
- 使用预留实例券
- 监控资源使用情况

---

## 九、文档变更记录

| 版本 | 日期 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 1.0 | 2026-03-26 | 初始版本 | - |
