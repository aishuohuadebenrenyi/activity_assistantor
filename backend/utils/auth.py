from functools import wraps
from flask import request, jsonify, current_app
import jwt
from ..models import User

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': '未提供认证令牌'}), 401
            
        try:
            # Token format: "Bearer <token>"
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': '用户不存在'}), 401
            
            # Inject user into request context
            request.user = user
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '令牌已过期'}), 401
        except (jwt.InvalidTokenError, IndexError):
            return jsonify({'error': '无效的令牌'}), 401
            
        return f(*args, **kwargs)
        
    return decorated
