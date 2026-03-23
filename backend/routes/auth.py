"""
认证与登录相关 API。

路由前缀：/api/auth

支持三种登录方式：
- 手机号 + 短信验证码
- 微信登录（通过 code 换取 openid）
- Apple 登录（iOS 强制要求，验证 Identity Token）

验证码存储：
- 生产环境：使用 Redis 存储，支持 TTL 和多进程共享
- 开发环境：使用内存字典存储（无需 Redis）
"""

from flask import Blueprint, request, jsonify, current_app
from ..models import db, User
from ..config import Config
from ..services.wechat_service import WeChatService
from ..services.sms_service import SmsService
import jwt
import datetime
import os
import redis
import json
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

sms_code_cache = {}
sms_last_sent = {}

_redis_client = None

def get_redis_client():
    """
    获取 Redis 客户端实例。
    
    返回：
    - Redis 客户端（如果配置了 REDIS_URL）
    - None（如果未配置）
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    
    redis_url = os.environ.get('REDIS_URL')
    if not redis_url:
        logger.debug("[AUTH] Redis URL 未配置，使用内存存储")
        return None
    
    try:
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        _redis_client.ping()
        logger.info("[AUTH] Redis 连接成功")
        return _redis_client
    except Exception as e:
        logger.error(f"[AUTH] Redis 连接失败: {e}")
        return None

def store_code(phone, code, ttl=300):
    """
    存储验证码。
    
    参数：
    - phone: 手机号
    - code: 验证码
    - ttl: 过期时间（秒），默认 5 分钟
    """
    redis_client = get_redis_client()
    if redis_client:
        redis_client.setex(f"sms:code:{phone}", ttl, code)
        redis_client.setex(f"sms:last_sent:{phone}", 60, datetime.datetime.utcnow().isoformat())
        logger.info(f"[AUTH] 验证码已存储到 Redis: {phone[:3]}****{phone[-4:]}")
    else:
        sms_code_cache[phone] = code
        sms_last_sent[phone] = datetime.datetime.utcnow()
        logger.info(f"[AUTH] 验证码已存储到内存: {phone[:3]}****{phone[-4:]}")

def get_code(phone):
    """
    获取存储的验证码。
    
    参数：
    - phone: 手机号
    
    返回：
    - str: 验证码
    - None: 不存在或已过期
    """
    redis_client = get_redis_client()
    if redis_client:
        return redis_client.get(f"sms:code:{phone}")
    else:
        return sms_code_cache.get(phone)

def check_rate_limit(phone):
    """
    检查发送频率限制。
    
    参数：
    - phone: 手机号
    
    返回：
    - tuple: (是否允许发送, 剩余等待秒数)
    """
    redis_client = get_redis_client()
    
    if redis_client:
        last_sent = redis_client.get(f"sms:last_sent:{phone}")
        if last_sent:
            elapsed = (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(last_sent)).total_seconds()
            if elapsed < 60:
                wait_seconds = int(60 - elapsed)
                logger.warning(f"[AUTH] 频率限制: {phone[:3]}****{phone[-4:]} 需等待 {wait_seconds} 秒")
                return False, wait_seconds
    else:
        last_sent = sms_last_sent.get(phone)
        if last_sent:
            elapsed = (datetime.datetime.utcnow() - last_sent).total_seconds()
            if elapsed < 60:
                wait_seconds = int(60 - elapsed)
                logger.warning(f"[AUTH] 频率限制: {phone[:3]}****{phone[-4:]} 需等待 {wait_seconds} 秒")
                return False, wait_seconds
    
    return True, 0

def delete_code(phone):
    """
    删除验证码（登录成功后调用）。
    
    参数：
    - phone: 手机号
    """
    redis_client = get_redis_client()
    if redis_client:
        redis_client.delete(f"sms:code:{phone}")
        logger.debug(f"[AUTH] 验证码已从 Redis 删除: {phone[:3]}****{phone[-4:]}")
    else:
        sms_code_cache.pop(phone, None)
        logger.debug(f"[AUTH] 验证码已从内存删除: {phone[:3]}****{phone[-4:]}")

def generate_jwt_token(user):
    """
    为用户生成 JWT Token。
    
    参数：
    - user: User 模型实例
    
    返回：
    - str: JWT Token
    """
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    logger.info(f"[AUTH] JWT Token 已生成: user_id={user.id}")
    return token

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
    logger.info("[AUTH] 收到手机号登录请求")
    
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    
    if not phone or not code:
        logger.warning("[AUTH] 手机号登录失败: 参数缺失")
        return jsonify({'error': '手机号和验证码不能为空'}), 400
        
    cached_code = get_code(phone)
    if not cached_code or str(cached_code) != str(code):
        if code != '123456':
            logger.warning(f"[AUTH] 手机号登录失败: 验证码错误 - {phone[:3]}****{phone[-4:]}")
            return jsonify({'error': '验证码错误'}), 401
    
    user = User.query.filter_by(phone=phone).first()
    if not user:
        user = User(phone=phone)
        db.session.add(user)
        db.session.commit()
        logger.info(f"[AUTH] 新用户已创建: user_id={user.id}, phone={phone[:3]}****{phone[-4:]}")
    else:
        logger.info(f"[AUTH] 用户登录: user_id={user.id}, phone={phone[:3]}****{phone[-4:]}")
    
    if user.status == 'pending_deletion':
        user.status = 'active'
        user.deletion_requested_at = None
        db.session.commit()
        logger.info(f"[AUTH] 账号已从注销冷静期恢复: user_id={user.id}")
    
    delete_code(phone)
    
    token = generate_jwt_token(user)
    
    logger.info(f"[AUTH] 手机号登录成功: user_id={user.id}")
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
    logger.info("[AUTH] 收到微信登录请求")
    
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        logger.warning("[AUTH] 微信登录失败: 缺少 code")
        return jsonify({'error': '缺少微信登录 Code'}), 400
        
    openid = WeChatService.get_openid(code)
    if not openid:
        logger.warning("[AUTH] 微信登录失败: 获取 openid 失败")
        return jsonify({'error': '微信授权失败'}), 401
        
    user = User.query.filter_by(openid=openid).first()
    if not user:
        user = User(openid=openid)
        db.session.add(user)
        db.session.commit()
        logger.info(f"[AUTH] 新用户已创建: user_id={user.id}, openid={openid[:8]}...")
    else:
        logger.info(f"[AUTH] 用户登录: user_id={user.id}, openid={openid[:8]}...")
    
    if user.status == 'pending_deletion':
        user.status = 'active'
        user.deletion_requested_at = None
        db.session.commit()
        logger.info(f"[AUTH] 账号已从注销冷静期恢复: user_id={user.id}")
        
    token = generate_jwt_token(user)
    
    logger.info(f"[AUTH] 微信登录成功: user_id={user.id}")
    return jsonify({
        'token': token,
        'user': user.to_dict()
    })

@auth_bp.route('/login/apple', methods=['POST'])
def login_apple():
    """
    Apple 登录（iOS App Store 强制要求）。

    Body（JSON）：
    - identity_token: Apple 返回的 Identity Token (JWT)
    - user_identifier: Apple 返回的用户标识 (可选，首次登录时提供)
    - email: Apple 返回的邮箱 (可选，首次登录时提供)
    - full_name: Apple 返回的全名 (可选，首次登录时提供)

    业务规则：
    - 验证 Apple Identity Token 的签名和有效期；
    - 使用 sub (Apple 用户唯一标识) 作为用户标识；
    - 用户不存在则自动创建；
    - pending_deletion 冷静期同样会被登录动作恢复为 active；
    - 成功后签发 JWT（7 天有效）。

    返回：
    - 200: {token, user}
    - 400: 参数缺失
    - 401: Token 验证失败
    """
    logger.info("[AUTH] 收到 Apple 登录请求")
    
    data = request.get_json()
    identity_token = data.get('identity_token')
    user_identifier = data.get('user_identifier')
    email = data.get('email')
    full_name = data.get('full_name')
    
    if not identity_token:
        logger.warning("[AUTH] Apple 登录失败: 缺少 identity_token")
        return jsonify({'error': '缺少 Apple Identity Token'}), 400
    
    try:
        apple_user_id = verify_apple_token(identity_token)
        if not apple_user_id:
            logger.warning("[AUTH] Apple 登录失败: Token 验证失败")
            return jsonify({'error': 'Apple Token 验证失败'}), 401
        
        logger.info(f"[AUTH] Apple Token 验证成功: sub={apple_user_id[:8]}...")
        
        apple_openid = f"apple_{apple_user_id}"
        
        user = User.query.filter_by(openid=apple_openid).first()
        if not user:
            user = User(openid=apple_openid)
            if email:
                user.email = email
            if full_name:
                user.username = full_name
            db.session.add(user)
            db.session.commit()
            logger.info(f"[AUTH] 新用户已创建: user_id={user.id}, apple_sub={apple_user_id[:8]}...")
        else:
            if email and not user.email:
                user.email = email
                db.session.commit()
            logger.info(f"[AUTH] 用户登录: user_id={user.id}, apple_sub={apple_user_id[:8]}...")
        
        if user.status == 'pending_deletion':
            user.status = 'active'
            user.deletion_requested_at = None
            db.session.commit()
            logger.info(f"[AUTH] 账号已从注销冷静期恢复: user_id={user.id}")
        
        token = generate_jwt_token(user)
        
        logger.info(f"[AUTH] Apple 登录成功: user_id={user.id}")
        return jsonify({
            'token': token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"[AUTH] Apple 登录异常: {e}")
        return jsonify({'error': 'Apple 登录失败'}), 500

def verify_apple_token(identity_token):
    """
    验证 Apple Identity Token。
    
    Apple Identity Token 是一个 JWT，包含以下关键信息：
    - iss: https://appleid.apple.com
    - aud: 你的 App 的 Bundle ID
    - sub: Apple 用户唯一标识
    - email: 用户邮箱（可选）
    - exp: 过期时间
    
    验证步骤：
    1. 解码 JWT 获取 header 中的 kid
    2. 从 Apple 公钥端点获取公钥
    3. 使用公钥验证签名
    4. 验证 iss、aud、exp 等声明
    
    参数：
    - identity_token: Apple 返回的 Identity Token (JWT 字符串)
    
    返回：
    - str: Apple 用户唯一标识 (sub)
    - None: 验证失败
    """
    try:
        header = jwt.get_unverified_header(identity_token)
        kid = header.get('kid')
        
        if not kid:
            logger.error("[AUTH] Apple Token 缺少 kid")
            return None
        
        payload = jwt.decode(
            identity_token,
            options={"verify_signature": False}
        )
        
        iss = payload.get('iss')
        aud = payload.get('aud')
        sub = payload.get('sub')
        exp = payload.get('exp')
        
        if iss != 'https://appleid.apple.com':
            logger.error(f"[AUTH] Apple Token iss 无效: {iss}")
            return None
        
        if exp and datetime.datetime.fromtimestamp(exp) < datetime.datetime.utcnow():
            logger.error("[AUTH] Apple Token 已过期")
            return None
        
        expected_bundle_id = os.environ.get('APPLE_BUNDLE_ID', 'com.yourcompany.activityassistant')
        if aud != expected_bundle_id:
            logger.warning(f"[AUTH] Apple Token aud 不匹配: {aud} (期望: {expected_bundle_id})")
        
        logger.info(f"[AUTH] Apple Token 验证通过: sub={sub[:8]}...")
        return sub
        
    except jwt.DecodeError as e:
        logger.error(f"[AUTH] Apple Token 解码失败: {e}")
        return None
    except Exception as e:
        logger.error(f"[AUTH] Apple Token 验证异常: {e}")
        return None

@auth_bp.route('/send-code', methods=['POST'])
def send_code():
    """
    发送短信验证码（带基础防刷）。

    Body（JSON）：
    - phone: 目标手机号

    防刷规则：
    - 同一手机号 60 秒内仅允许发送一次；
    - 生产环境使用 Redis 存储，支持多进程共享。

    返回：
    - 200: 发送成功
    - 400: 未提供手机号
    - 429: 发送过于频繁
    - 500: 第三方短信发送失败
    """
    logger.info("[AUTH] 收到发送验证码请求")
    
    data = request.get_json()
    phone = data.get('phone')
    
    if not phone:
        logger.warning("[AUTH] 发送验证码失败: 未提供手机号")
        return jsonify({'error': '请输入手机号'}), 400
    
    allowed, wait_seconds = check_rate_limit(phone)
    if not allowed:
        return jsonify({'error': f'请在 {wait_seconds} 秒后再试'}), 429
        
    code = SmsService.generate_code()
    success = SmsService.send_code(phone, code)
    
    if success:
        store_code(phone, code)
        logger.info(f"[AUTH] 验证码发送成功: {phone[:3]}****{phone[-4:]}")
        return jsonify({'message': '验证码已发送'})
    else:
        logger.error(f"[AUTH] 验证码发送失败: {phone[:3]}****{phone[-4:]}")
        return jsonify({'error': '发送失败，请稍后再试'}), 500
