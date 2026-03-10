# 导入 Flask 核心库
from flask import Flask
# 导入 CORS 扩展，用于处理跨域请求
from flask_cors import CORS
# 导入配置类
from .config import Config
# 导入数据库实例
from .models import db
# 导入各个功能模块的蓝图 (Blueprint)
from .routes.auth import auth_bp
from .routes.activity import activity_bp
from .routes.participant import participant_bp
from .routes.user import user_bp

def create_app():
    """
    创建并配置 Flask 应用实例
    """
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(Config)
    
    # 初始化扩展
    # 初始化数据库连接
    db.init_app(app)
    # 启用 CORS，允许跨域访问
    CORS(app)
    
    # 注册蓝图 (Blueprints)
    # 认证模块：处理登录、注册等
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    # 活动模块：处理活动的增删改查
    app.register_blueprint(activity_bp, url_prefix='/api/activities')
    # 参与者模块：处理报名、签到等，根路径为 /api，具体路由可能包含 activity_id
    app.register_blueprint(participant_bp, url_prefix='/api') 
    # 用户模块：处理个人信息、我的活动等
    app.register_blueprint(user_bp, url_prefix='/api/user')
    
    # 创建数据库表
    # 注意：在生产环境中，通常使用 Flask-Migrate 进行数据库迁移，而不是每次启动都 create_all
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
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)
