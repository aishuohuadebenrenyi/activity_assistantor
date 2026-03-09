from flask import Blueprint, request, jsonify
from ..models import db, User
from ..config import Config
import jwt
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    
    # Simple validation: In real world, verify code from Redis/Cache
    if not phone or not code:
        return jsonify({'error': '手机号和验证码不能为空'}), 400
        
    if code != '123456': # Mock verification
        return jsonify({'error': '验证码错误'}), 401
        
    user = User.query.filter_by(phone=phone).first()
    if not user:
        user = User(phone=phone)
        db.session.add(user)
        db.session.commit()
        
    # Generate Token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, Config.SECRET_KEY, algorithm='HS256')
    
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
        
    # Mock SMS sending
    print(f"Sending code 123456 to {phone}")
    
    return jsonify({'message': '验证码已发送'})
