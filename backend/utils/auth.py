from functools import wraps
from flask import request, current_app
import jwt
from ..models import User
from .errors import error_response

def auth_required(f):
    """
    JWT 鉴权装饰器（Bearer Token）。

    使用方式：
    - 在需要登录态的路由上添加 `@auth_required`；
    - 客户端通过 Header 传入：`Authorization: Bearer <token>`。

    行为：
    - 解析并校验 JWT（HS256，密钥来自 `current_app.config['SECRET_KEY']`）；
    - 将数据库中的用户对象注入到 `request.user`，供业务函数直接使用；
    - 对常见失败场景返回统一错误码：
      - 未携带 token：AUTH_UNAUTHORIZED (401)
      - token 过期：AUTH_TOKEN_EXPIRED (401)
      - token 非法/格式错误/用户不存在：AUTH_UNAUTHORIZED (401)

    注意：
    - 该实现把用户对象挂载到 `request` 上，属于工程约定；如引入更复杂鉴权建议迁移到 Flask g/contextvars。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return error_response("AUTH_UNAUTHORIZED", "未提供认证令牌", status=401)
            
        try:
            # Token format: "Bearer <token>"
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
            user = User.query.get(user_id)
            if not user:
                return error_response("AUTH_UNAUTHORIZED", "用户不存在", status=401)
            
            # Inject user into request context
            request.user = user
        except jwt.ExpiredSignatureError:
            return error_response("AUTH_TOKEN_EXPIRED", "令牌已过期", status=401)
        except (jwt.InvalidTokenError, IndexError):
            return error_response("AUTH_UNAUTHORIZED", "无效的令牌", status=401)
            
        return f(*args, **kwargs)
        
    return decorated
