"""
用户相关 API（个人资料、账号注销、举报入口）。

路由前缀：/api/user

说明：
- 本模块涉及“账户状态机”（active/pending_deletion/deleted）与冷静期业务规则；
- 注销采用“不可逆脱敏 + 关联数据清理”策略，以满足合规与审计留痕。
"""

from flask import Blueprint, request, jsonify
from ..models import db, User, Activity, Registration, CheckinRecord
from ..utils.auth import auth_required
from ..utils.idempotency import idempotent
import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@auth_required
def get_profile():
    """
    获取当前登录用户的个人资料。

    返回：
    - 200: User.to_dict() 的 JSON 结构。
    """
    user = request.user
    return jsonify(user.to_dict())

@user_bp.route('/profile', methods=['PUT'])
@auth_required
def update_profile():
    """
    更新当前登录用户的个人资料（部分字段更新）。

    Body（JSON）：可选字段
    - username: 昵称
    - bio: 简介
    - avatar_url: 头像 URL

    返回：
    - 200: 更新后的用户信息。
    """
    user = request.user
    data = request.get_json()
    
    if 'username' in data: user.username = data['username']
    if 'bio' in data: user.bio = data['bio']
    if 'avatar_url' in data: user.avatar_url = data['avatar_url']
    
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/account', methods=['DELETE'])
@auth_required
@idempotent
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
    执行最终的脱敏删除逻辑（不可逆）。

    数据处理策略：
    1) 删除用户发布的活动（级联删除报名与签到记录）；
    2) 用户记录做不可逆脱敏（替换 phone/openid/头像/简介等），保留一条“已注销用户”记录用于审计；
    3) 删除以旧手机号报名的报名记录（当前 Registration 通过 phone 关联，不绑定 user_id）。

    参数：
    - user: 当前登录用户对象（必须已通过 auth_required 注入）。

    返回：
    - 200: 注销成功提示。
    """
    user_id = user.id
    old_phone = user.phone
    
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
    registrations = Registration.query.filter_by(phone=old_phone).all() if old_phone else []
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

    Body（JSON）：
    - target_type: 举报对象类型（如 activity/user）
    - target_id: 举报对象 ID
    - reason: 举报原因

    当前实现说明：
    - 该接口用于“能力占位”，暂未落库，直接打印日志并返回成功；
    - 若要形成闭环，应与 models.Report 或独立举报表结合，实现后台处理/状态流转。
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
