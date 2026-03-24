# 导入 Flask 核心库
import os
from flask import Flask, send_from_directory, request
# 导入 CORS 扩展，用于处理跨域请求
from flask_cors import CORS
# 导入安全限制库
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.exceptions import HTTPException
# 导入配置类
from .config import Config
# 导入数据库实例
from .models import db
# 导入 request_id 与错误响应
from .utils.request_id import init_request_id
from .utils.errors import error_response
# 导入各个功能模块的蓝图 (Blueprint)
from .routes.auth import auth_bp
from .routes.activity import activity_bp
from .routes.participant import participant_bp
from .routes.user import user_bp
from .routes.org import org_bp
from .routes.billing import billing_bp
from .routes.support import support_bp
from .routes.analytics import analytics_bp

def create_app(config_class=Config):
    """
    创建并配置 Flask 应用实例（应用工厂模式）。

    主要职责：
    - 加载配置（数据库、密钥、第三方服务开关等）；
    - 初始化 Flask 扩展（SQLAlchemy/CORS/限流/安全头等）；
    - 初始化链路追踪 request_id（生成/透传/回传 `X-Request-Id`）；
    - 注册所有业务 Blueprint 到统一 `/api` 前缀下；
    - 对 `/api` 路径提供统一异常到错误码的转换，保证响应结构稳定；
    - 非测试环境下自动建表（便于 demo/本地运行）。

    参数：
    - config_class: 配置类，默认使用 `backend.config.Config`。

    返回：
    - Flask: 配置完成的 Flask app 实例。
    """
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config_class)
    
    # 初始化扩展
    # 初始化数据库连接
    db.init_app(app)
    # 启用 CORS，允许跨域访问
    CORS(app)

    init_request_id(app)
    
    storage_uri = app.config.get('REDIS_URL') or "memory://"
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=storage_uri,
    )
    
    # 启用 Talisman (强制 HTTPS, 设置安全响应头)
    # 生产环境必须启用 HTTPS：force_https=True
    # 开发环境可以设置 force_https=False
    force_https = os.environ.get('FORCE_HTTPS', 'false').lower() == 'true'
    Talisman(app, force_https=force_https) 
    
    # 注册蓝图 (Blueprints)
    # 认证模块：处理登录、注册等
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    # 活动模块：处理活动的增删改查
    app.register_blueprint(activity_bp, url_prefix='/api/activities')
    # 参与者模块：处理报名、签到等，注册在 /api/activities 下，共享前缀
    app.register_blueprint(participant_bp, url_prefix='/api/activities') 
    # 用户模块：处理个人信息、我的活动等
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(org_bp, url_prefix='/api/org')
    app.register_blueprint(billing_bp, url_prefix='/api/billing')
    app.register_blueprint(support_bp, url_prefix='/api/support')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    # 创建数据库表 (仅在非测试模式下自动创建)
    if not app.config.get('TESTING'):
        with app.app_context():
            db.create_all()

    @app.errorhandler(HTTPException)
    def _handle_http_exc(e):
        if request.path.startswith("/api"):
            code_map = {
                400: "REQ_INVALID",
                401: "AUTH_UNAUTHORIZED",
                403: "AUTH_FORBIDDEN",
                404: "NOT_FOUND",
                409: "CONFLICT",
                422: "REQ_INVALID",
                429: "RATE_LIMITED",
            }
            return error_response(code_map.get(e.code, f"HTTP_{e.code}"), e.description, status=e.code)
        return e

    @app.errorhandler(Exception)
    def _handle_uncaught(e):
        if request.path.startswith("/api"):
            return error_response("INTERNAL_ERROR", "服务器开小差了，请稍后再试", status=500)
        raise e

    # 根路由：用于健康检查
    @app.route('/')
    def index():
        return {
            "status": "online",
            "message": "Activity Assistant Backend API is running",
            "docs": "/api/activities"
        }

    @app.route('/health')
    def health():
        return {
            "status": "ok",
            "service": "activity-assistant-api"
        }

    @app.route('/legal/privacy', strict_slashes=False)
    def legal_privacy():
        legal_dir = os.path.join(app.root_path, 'static', 'legal')
        return send_from_directory(legal_dir, 'privacy.html')

    @app.route('/legal/terms', strict_slashes=False)
    def legal_terms():
        legal_dir = os.path.join(app.root_path, 'static', 'legal')
        return send_from_directory(legal_dir, 'terms.html')
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)
