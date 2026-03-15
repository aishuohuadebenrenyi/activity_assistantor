"""
认证与登录相关 API。

路由前缀：/api/auth

支持两种登录方式：
- 手机号 + 短信验证码；
- 微信登录（通过 code 换取 openid）。

注意：
- 当前验证码缓存与发送频控为内存字典实现，仅适用于单进程开发/演示环境；
- 生产环境应替换为 Redis 等带 TTL 的持久化缓存，并结合网关/风控做更强防刷。
"""

from flask import Blueprint, request, jsonify, current_app
from ..models import db, User
from ..config import Config
from ..services.wechat_service import WeChatService
from ..services.sms_service import SmsService
import jwt
import datetime

auth_bp = Blueprint('auth', __name__)

# Simple in-memory cache for verification codes and rate limiting.
# In production, use Redis for persistence and TTL.
sms_code_cache = {}
sms_last_sent = {} # {phone: timestamp}

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    手机号验证码登录/注册。

    Body（JSON）：
    - phone: 手机号
    - code: 验证码（开发/测试允许使用 123456 作为兜底）

    业务规则：
    - 用户不存在则自动创建；
    - 若用户处于 pending_deletion 冷静期，登录会自动恢复账号为 active；
    - 登录成功签发 JWT（7 天有效）。

    返回：
    - 200: {token, user}
    - 400: 参数缺失
    - 401: 验证码错误
    """
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    
    if not phone or not code:
        return jsonify({'error': '手机号和验证码不能为空'}), 400
        
    # Verify code
    cached_code = sms_code_cache.get(phone)
    if not cached_code or str(cached_code) != str(code):
        # Fallback for mock/test if needed
        if code != '123456':
             return jsonify({'error': '验证码错误'}), 401
        
    user = User.query.filter_by(phone=phone).first()
    if not user:
        user = User(phone=phone)
        db.session.add(user)
        db.session.commit()
    
    # 冷静期内登录自动恢复账号
    if user.status == 'pending_deletion':
        user.status = 'active'
        user.deletion_requested_at = None
        db.session.commit()
        
    # Generate Token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        'token': token,
        'user': user.to_dict()
    })

@auth_bp.route('/login/wechat', methods=['POST'])
def login_wechat():
    """
    微信登录（小程序/APP 的 code 换取 openid）。

    Body（JSON）：
    - code: 微信登录 code

    业务规则：
    - 通过微信接口换取 openid；
    - openid 未绑定用户则创建用户；
    - pending_deletion 冷静期同样会被登录动作恢复为 active；
    - 成功后签发 JWT（7 天有效）。

    返回：
    - 200: {token, user}
    - 400: 缺少 code
    - 401: 微信授权失败
    """
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'error': '缺少微信登录 Code'}), 400
        
    openid = WeChatService.get_openid(code)
    if not openid:
        return jsonify({'error': '微信授权失败'}), 401
        
    user = User.query.filter_by(openid=openid).first()
    if not user:
        user = User(openid=openid)
        db.session.add(user)
        db.session.commit()
    
    # 冷静期内登录自动恢复账号
    if user.status == 'pending_deletion':
        user.status = 'active'
        user.deletion_requested_at = None
        db.session.commit()
        
    # Generate Token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        'token': token,
        'user': user.to_dict()
    })

@auth_bp.route('/send-code', methods=['POST'])
def send_code():
    """
    发送短信验证码（带基础防刷）。

    Body（JSON）：
    - phone: 目标手机号

    防刷规则（当前实现）：
    - 同一手机号 60 秒内仅允许发送一次；
    - 缓存写入 sms_code_cache/sms_last_sent（进程内存）。

    返回：
    - 200: 发送成功
    - 400: 未提供手机号
    - 429: 发送过于频繁
    - 500: 第三方短信发送失败
    """
    data = request.get_json()
    phone = data.get('phone')
    
    if not phone:
        return jsonify({'error': '请输入手机号'}), 400
    
    # 防刷机制：同一个手机号 60 秒内只能发送一次
    last_sent = sms_last_sent.get(phone)
    if last_sent:
        elapsed = (datetime.datetime.utcnow() - last_sent).total_seconds()
        if elapsed < 60:
            return jsonify({'error': f'请在 {int(60 - elapsed)} 秒后再试'}), 429
        
    code = SmsService.generate_code()
    success = SmsService.send_code(phone, code)
    
    if success:
        sms_code_cache[phone] = code
        sms_last_sent[phone] = datetime.datetime.utcnow()
        return jsonify({'message': '验证码已发送'})
    else:
        return jsonify({'error': '发送失败，请稍后再试'}), 500
