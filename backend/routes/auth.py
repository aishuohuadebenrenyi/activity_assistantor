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
