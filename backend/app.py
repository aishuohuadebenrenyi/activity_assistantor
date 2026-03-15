# 导入 Flask 核心库
import os
from flask import Flask, send_from_directory
# 导入 CORS 扩展，用于处理跨域请求
from flask_cors import CORS
# 导入安全限制库
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
# 导入配置类
from .config import Config
# 导入数据库实例
from .models import db
# 导入各个功能模块的蓝图 (Blueprint)
from .routes.auth import auth_bp
from .routes.activity import activity_bp
from .routes.participant import participant_bp
from .routes.user import user_bp

def create_app(config_class=Config):
    """
    创建并配置 Flask 应用实例
    """
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config_class)
    
    # 初始化扩展
    # 初始化数据库连接
    db.init_app(app)
    # 启用 CORS，允许跨域访问
    CORS(app)
    
    # 初始化安全限制 (频率限制)
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )
    
    # 启用 Talisman (强制 HTTPS, 设置安全响应头)
    # 注意：在开发环境下如果不用 HTTPS，可以设置 force_https=False
    Talisman(app, force_https=False) 
    
    # 注册蓝图 (Blueprints)
    # 认证模块：处理登录、注册等
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    # 活动模块：处理活动的增删改查
    app.register_blueprint(activity_bp, url_prefix='/api/activities')
    # 参与者模块：处理报名、签到等，注册在 /api/activities 下，共享前缀
    app.register_blueprint(participant_bp, url_prefix='/api/activities') 
    # 用户模块：处理个人信息、我的活动等
    app.register_blueprint(user_bp, url_prefix='/api/user')
    
    # 创建数据库表 (仅在非测试模式下自动创建)
    if not app.config.get('TESTING'):
        with app.app_context():
            db.create_all()

    # 根路由：用于健康检查
    @app.route('/')
    def index():
        return {
            "status": "online",
            "message": "Activity Assistant Backend API is running",
            "docs": "/api/activities"
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
