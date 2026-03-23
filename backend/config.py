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

    # 数据库连接池配置 (适用于 FC 部署场景)
    # 连接池大小：FC 单实例并发有限，连接池不宜过大
    SQLALCHEMY_POOL_SIZE = int(os.environ.get('SQLALCHEMY_POOL_SIZE', 5))
    # 连接回收时间：FC 实例可能长时间不活动，需定期回收连接
    SQLALCHEMY_POOL_RECYCLE = int(os.environ.get('SQLALCHEMY_POOL_RECYCLE', 300))
    # 连接健康检查：每次使用前检查连接是否有效
    SQLALCHEMY_POOL_PRE_PING = True
    # 最大溢出连接数
    SQLALCHEMY_MAX_OVERFLOW = int(os.environ.get('SQLALCHEMY_MAX_OVERFLOW', 2))

    # 禁用 SQLAlchemy 修改跟踪，以减少内存开销
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis 连接配置
    # 用于验证码存储、限流计数、Session 缓存等
    REDIS_URL = os.environ.get('REDIS_URL')
    
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
