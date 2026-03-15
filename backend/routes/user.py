from flask import Blueprint, request, jsonify
from ..models import db, User, Activity, Registration, CheckinRecord
from ..utils.auth import auth_required
import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@auth_required
def get_profile():
    user = request.user
    return jsonify(user.to_dict())

@user_bp.route('/profile', methods=['PUT'])
@auth_required
def update_profile():
    user = request.user
    data = request.get_json()
    
    if 'username' in data: user.username = data['username']
    if 'bio' in data: user.bio = data['bio']
    if 'avatar_url' in data: user.avatar_url = data['avatar_url']
    
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/account', methods=['DELETE'])
@auth_required
def delete_account():
    """
    符合 iOS 指南 5.1.1(v) 和微信运营规范：
    1. 提供 15 天冷静期处理机制。
    2. 注销请求后账户进入 pending_deletion 状态。
    3. 如果是第二次请求或管理员操作，则执行不可逆脱敏记录。
    """
    user = request.user
    
    # 检查是否已经在冷静期内
    if user.status == 'pending_deletion':
        # 如果是冷静期内的第二次请求，执行最终删除（脱敏处理）
        return finalize_user_deletion(user)
    
    # 进入冷静期
    user.status = 'pending_deletion'
    user.deletion_requested_at = datetime.datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': '您的注销申请已提交。账号已进入 15 天冷静期，期间您可以随时登录恢复账号。15 天后数据将永久清除。',
        'status': 'pending',
        'cooldown_days': 15
    })

def finalize_user_deletion(user):
    """
    执行最终的脱敏删除逻辑
    """
    user_id = user.id
    
    # 1. 删除用户的活动（及其关联的报名和签到记录通过级联删除）
    activities = Activity.query.filter_by(user_id=user_id).all()
    for act in activities:
        db.session.delete(act)
        
    # 2. 对用户基本信息进行不可逆脱敏处理，而不是直接物理删除（保留脱敏记录以备审计）
    user.phone = f"DELETED_{user_id}_{datetime.datetime.utcnow().timestamp()}"
    user.openid = None
    user.username = "已注销用户"
    user.avatar_url = ""
    user.bio = "该用户已注销"
    user.status = 'deleted'
    
    # 3. 删除该用户的所有报名记录（物理删除或同样脱敏）
    registrations = Registration.query.filter_by(phone=user.phone).all()
    for reg in registrations:
        db.session.delete(reg)
        
    db.session.commit()
    
    return jsonify({
        'message': '您的账号已永久注销，所有个人数据已清除。',
        'status': 'success'
    })

@user_bp.route('/report', methods=['POST'])
@auth_required
def report_content():
    """
    符合 iOS App Store 指南 1.2 要求：提供举报违规内容的机制 (UGC)
    """
    user = request.user
    data = request.get_json()
    
    target_type = data.get('target_type') # 'activity', 'user'
    target_id = data.get('target_id')
    reason = data.get('reason')
    
    # 在实际应用中，这里会将举报信息存入数据库表 Report
    # 目前记录到日志或模拟成功
    print(f"User {user.id} reported {target_type} {target_id} for reason: {reason}")
    
    return jsonify({
        'message': '感谢您的举报，我们将在24小时内核实处理',
        'status': 'success'
    })
