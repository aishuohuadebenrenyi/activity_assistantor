import os

class Config:
    """
    Flask 应用配置类。

    该类统一管理应用的所有配置项。配置项加载遵循以下优先级：
    1. 环境变量：适配云原生部署环境（如阿里云函数计算 FC、Docker 等）；
    2. 默认值：仅用于本地开发和快速演示。

    安全规范：
    - 生产环境严禁使用默认密钥，必须通过环境变量注入 SECRET_KEY、WECHAT_SECRET 等敏感信息。
    - 严禁将包含真实密钥的配置文件提交至版本控制系统。
    """
    # 应用安全密钥，用于 Session 加密、JWT 签名等
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'

    # 数据库连接 URI
    # 默认使用本地 SQLite 数据库 (app.db)，生产环境建议使用云数据库（如 RDS MySQL/PostgreSQL）
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'

    # 禁用 SQLAlchemy 修改跟踪，以减少内存开销
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 阿里云函数计算 (FC) 服务名称配置
    # 用于识别当前运行的云服务上下文，支持日志链路追踪及多环境隔离
    FC_SERVICE_NAME = os.environ.get('FC_SERVICE_NAME')

    # 微信小程序配置
    # WECHAT_APPID: 小程序唯一标识
    WECHAT_APPID = os.environ.get('WECHAT_APPID') or 'wx1234567890abcdef'
    # WECHAT_SECRET: 小程序应用密钥，需严格保密
    WECHAT_SECRET = os.environ.get('WECHAT_SECRET') or 'wx1234567890abcdef1234567890abcdef'

    # 客服中心跳转 URL
    # 用于前端跳转至外部客服系统或 H5 帮助页面
    CUSTOMER_SERVICE_URL = os.environ.get('CUSTOMER_SERVICE_URL') or ''
