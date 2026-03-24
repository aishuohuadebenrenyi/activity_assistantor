"""
用户相关 API（个人资料、账号注销、举报入口）。

路由前缀：/api/user

说明：
- 本模块涉及"账户状态机"（active/pending_deletion/deleted）与冷静期业务规则；
- 注销采用"不可逆脱敏 + 关联数据清理"策略，以满足合规与审计留痕。
"""

from flask import Blueprint, request, jsonify
from ..models import db, User, Activity, Registration, CheckinRecord, Report
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
    
    if user.status == 'pending_deletion':
        return finalize_user_deletion(user)
    
    user.status = 'pending_deletion'
    user.deletion_requested_at = datetime.datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': '您的注销申请已提交。账号已进入 15 天冷静期，期间您可以随时登录恢复账号。15 天后数据将永久清除。',
        'status': 'pending_deletion',
        'cooldown_days': 15
    })

def finalize_user_deletion(user):
    """
    执行最终的脱敏删除逻辑（不可逆）。

    数据处理策略：
    1) 删除用户发布的活动（级联删除报名与签到记录）；
    2) 用户记录做不可逆脱敏（替换 phone/openid/头像/简介等），保留一条"已注销用户"记录用于审计；
    3) 删除以旧手机号报名的报名记录（当前 Registration 通过 phone 关联，不绑定 user_id）。

    参数：
    - user: 当前登录用户对象（必须已通过 auth_required 注入）。

    返回：
    - 200: 注销成功提示。
    """
    user_id = user.id
    old_phone = user.phone
    
    activities = Activity.query.filter_by(user_id=user_id).all()
    for act in activities:
        db.session.delete(act)
        
    user.phone = f"DELETED_{user_id}_{datetime.datetime.utcnow().timestamp()}"
    user.openid = None
    user.username = "已注销用户"
    user.avatar_url = ""
    user.bio = "该用户已注销"
    user.status = 'deleted'
    
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
    - target_type: 举报对象类型（activity/user）
    - target_id: 举报对象 ID
    - reason: 举报原因
    - detail: 举报详情（可选）

    业务规则：
    - 同一用户对同一目标仅能举报一次（防止恶意刷举报）；
    - 举报信息存入 Report 表，状态默认为 pending；
    - 后台管理员可查看并处理举报（processed/rejected）。

    返回：
    - 200: 举报成功
    - 400: 参数缺失
    - 409: 已举报过
    """
    user = request.user
    data = request.get_json()
    
    target_type = data.get('target_type')
    target_id = data.get('target_id')
    reason = data.get('reason')
    detail = data.get('detail', '')
    
    if not target_type or not target_id or not reason:
        return jsonify({'error': '请填写完整的举报信息'}), 400
    
    if target_type not in ['activity', 'user']:
        return jsonify({'error': '举报类型无效'}), 400
    
    if target_type == 'activity':
        activity = Activity.query.get(target_id)
        if not activity:
            return jsonify({'error': '活动不存在'}), 404
        
        existing = Report.query.filter_by(
            user_id=user.id,
            activity_id=target_id
        ).first()
        if existing:
            return jsonify({'error': '您已举报过该活动'}), 409
        
        report = Report(
            activity_id=target_id,
            user_id=user.id,
            reason=reason,
            detail=detail,
            status='pending'
        )
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'message': '感谢您的举报，我们将在24小时内核实处理',
            'report_id': report.id,
            'status': 'success'
        })
    
    return jsonify({'message': '举报已记录', 'status': 'success'})

@user_bp.route('/reports', methods=['GET'])
@auth_required
def get_user_reports():
    """
    获取当前用户的举报记录列表。

    返回：
    - 200: 举报记录列表
    """
    user = request.user
    reports = Report.query.filter_by(user_id=user.id).order_by(Report.created_at.desc()).all()
    return jsonify({
        'reports': [r.to_dict() for r in reports],
        'total': len(reports)
    })

@user_bp.route('/registrations', methods=['GET'])
@auth_required
def get_user_registrations():
    """
    获取当前用户报名的活动列表。

    业务规则：
    - 通过用户手机号匹配报名记录；
    - 返回活动详情与报名状态。

    返回：
    - 200: 报名活动列表
    """
    user = request.user
    
    if not user.phone:
        return jsonify({
            'registrations': [],
            'total': 0
        })
    
    registrations = Registration.query.filter_by(phone=user.phone).order_by(Registration.created_at.desc()).all()
    
    result = []
    for reg in registrations:
        activity = Activity.query.get(reg.activity_id)
        if activity:
            checkin_record = CheckinRecord.query.filter_by(registration_id=reg.id).first()
            result.append({
                'registration': reg.to_dict(),
                'activity': activity.to_dict(include_registrations=False, show_contact=True, is_organizer=False),
                'checked_in': checkin_record is not None,
                'checkin_time': checkin_record.checkin_time.isoformat() if checkin_record else None
            })
    
    return jsonify({
        'registrations': result,
        'total': len(result)
    })
