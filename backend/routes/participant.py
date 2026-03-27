"""
参与者相关 API（报名/名单/导出）。

路由前缀：/api/activities

说明：
- 该 Blueprint 注册在 `/api/activities` 下，因此路由形如：
  - GET  /api/activities/<activity_id>/participants
  - POST /api/activities/<activity_id>/register
  - POST /api/activities/<activity_id>/export
- 写接口接入幂等，配合前端离线队列重放避免重复报名/重复导出请求。
"""

from flask import Blueprint, request, jsonify, current_app
from ..models import db, Registration, CheckinRecord, Activity
from ..utils.auth import auth_required
from ..utils.idempotency import idempotent
from ..services.email_service import EmailService
import csv
import io

participant_bp = Blueprint('participant', __name__)

@participant_bp.route('/<int:activity_id>/participants', methods=['GET'])
@auth_required
def get_participants(activity_id):
    """
    获取活动报名名单（仅组织者可访问）。

    参数：
    - activity_id: 活动 ID（路径参数）

    返回：
    - 200: 报名数组，包含签到状态与签到时间（若已签到）；
    - 403: 非组织者无权限查看；
    - 404: 活动不存在。
    """
    activity = Activity.query.get_or_404(activity_id)
    if activity.user_id != request.user.id:
        return jsonify({'error': '没有权限查看报名名单'}), 403
    
    registrations = Registration.query.filter_by(activity_id=activity_id).all()
    
    result = []
    for reg in registrations:
        item = reg.to_dict()
        checkin = CheckinRecord.query.filter_by(registration_id=reg.id).first()
        if checkin:
            item['checkin_time'] = checkin.checkin_time.isoformat()
            item['checked_in'] = True
        else:
            item['checked_in'] = False
        result.append(item)
        
    return jsonify(result)

@participant_bp.route('/<int:activity_id>/register', methods=['POST'])
@auth_required
@idempotent
def register(activity_id):
    """
    报名活动（需要登录）。

    Body（JSON）：
    - name: 报名人姓名（必填）
    - phone: 报名人手机号（必填）

    业务规则：
    - 以 (activity_id, user_id) 判断重复报名（已登录用户）；
    - 以 (activity_id, phone) 判断重复报名（未关联用户场景）；
    - 校验活动状态（已结束的活动不可报名）；
    - 校验活动容量（名额已满不可报名）；
    - 自动关联当前登录用户的 user_id。

    返回：
    - 201: 报名成功，返回 Registration；
    - 400: 参数缺失、已报名、活动已结束或名额已满。
    """
    from datetime import datetime
    
    activity = Activity.query.get_or_404(activity_id)
    user = request.user
    
    if activity.status == 'ended':
        return jsonify({'error': '活动已结束，无法报名'}), 400
    
    if activity.start_time and activity.start_time < datetime.utcnow():
        return jsonify({'error': '活动已开始，无法报名'}), 400
    
    if activity.capacity > 0:
        current_count = Registration.query.filter_by(activity_id=activity_id).count()
        if current_count >= activity.capacity:
            return jsonify({'error': '活动名额已满'}), 400
    
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    
    if not name or not phone:
        return jsonify({'error': 'Missing name or phone'}), 400
    
    # 优先通过 user_id 检查重复报名
    if user.id:
        existing_by_user = Registration.query.filter_by(activity_id=activity_id, user_id=user.id).first()
        if existing_by_user:
            return jsonify({'error': '您已经报名过此活动'}), 400
    
    # 同时检查手机号重复（防止同一用户换手机号重复报名）
    existing_by_phone = Registration.query.filter_by(activity_id=activity_id, phone=phone).first()
    if existing_by_phone:
        return jsonify({'error': '该手机号已报名过此活动'}), 400
        
    reg = Registration(activity_id=activity_id, user_id=user.id, name=name, phone=phone)
    db.session.add(reg)
    db.session.commit()
    
    return jsonify(reg.to_dict()), 201

@participant_bp.route('/<int:activity_id>/register', methods=['DELETE'])
@auth_required
def cancel_registration(activity_id):
    """
    取消报名（需要登录）。

    业务规则：
    - 优先通过 user_id 匹配报名记录；
    - 若 user_id 未匹配，则通过 phone 匹配（兼容旧数据）；
    - 已签到的报名不可取消；
    - 活动已开始后不可取消。

    返回：
    - 200: 取消成功；
    - 400: 未报名、已签到或活动已开始；
    - 404: 活动不存在。
    """
    from datetime import datetime
    
    user = request.user
    activity = Activity.query.get_or_404(activity_id)
    
    # 优先通过 user_id 查找报名记录
    registration = Registration.query.filter_by(activity_id=activity_id, user_id=user.id).first()
    
    # 兼容旧数据：通过 phone 匹配
    if not registration and user.phone:
        registration = Registration.query.filter_by(activity_id=activity_id, phone=user.phone).first()
    
    if not registration:
        return jsonify({'error': '您尚未报名此活动'}), 400
    
    if activity.start_time and activity.start_time < datetime.utcnow():
        return jsonify({'error': '活动已开始，无法取消报名'}), 400
    
    checkin = CheckinRecord.query.filter_by(registration_id=registration.id).first()
    if checkin:
        return jsonify({'error': '您已签到，无法取消报名'}), 400
    
    db.session.delete(registration)
    db.session.commit()
    
    return jsonify({'message': '取消报名成功', 'activity_id': activity_id})

@participant_bp.route('/<int:activity_id>/export', methods=['POST'])
@auth_required
@idempotent
def export_participants(activity_id):
    """
    导出报名名单（仅组织者可访问）。

    Body（JSON）：
    - email: 接收导出的邮箱（必填）

    实现：
    - 以 CSV 格式生成内容；
    - 使用 EmailService 发送邮件（支持 Mock/生产双模式）；
    - 对外响应使用 202 Accepted，表示请求已受理。

    返回：
    - 202: 请求已受理；
    - 403/404: 权限或活动不存在；
    - 400: 未提供邮箱。
    """
    activity = Activity.query.get_or_404(activity_id)
    if activity.user_id != request.user.id:
        return jsonify({'error': '没有权限导出报名名单'}), 403
        
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': '未提供导出邮箱'}), 400
        
    registrations = Registration.query.filter_by(activity_id=activity_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '姓名', '电话', '报名时间', '是否签到', '签到时间'])
    
    for reg in registrations:
        checkin = CheckinRecord.query.filter_by(registration_id=reg.id).first()
        checked_in = "是" if checkin else "否"
        checkin_time = checkin.checkin_time.isoformat() if checkin else ""
        writer.writerow([reg.id, reg.name, reg.phone, reg.created_at.isoformat(), checked_in, checkin_time])
    
    csv_content = output.getvalue()
    
    success = EmailService.send_participant_export(email, activity.name, csv_content)
    
    if success:
        return jsonify({'message': '报名名单已发送至您的邮箱，请查收'}), 202
    else:
        return jsonify({'message': '导出请求已接收，报名名单将在3个工作日内发送至您的邮箱'}), 202

@participant_bp.route('/<int:activity_id>/checkin/<int:registration_id>', methods=['DELETE'])
@auth_required
def cancel_checkin(activity_id, registration_id):
    """
    取消签到（仅组织者可操作）。

    参数：
    - activity_id: 活动 ID（路径参数）
    - registration_id: 报名记录 ID（路径参数）

    业务规则：
    - 仅活动组织者可取消签到；
    - 签到记录被删除后，报名状态恢复为未签到。

    返回：
    - 200: 取消成功；
    - 403: 非组织者无权限；
    - 404: 活动或签到记录不存在。
    """
    activity = Activity.query.get_or_404(activity_id)
    if activity.user_id != request.user.id:
        return jsonify({'error': '没有权限操作'}), 403
    
    registration = Registration.query.get_or_404(registration_id)
    if registration.activity_id != activity_id:
        return jsonify({'error': '报名记录不属于该活动'}), 400
    
    checkin = CheckinRecord.query.filter_by(registration_id=registration_id).first()
    if not checkin:
        return jsonify({'error': '该报名尚未签到'}), 400
    
    db.session.delete(checkin)
    db.session.commit()
    
    return jsonify({'message': '签到已取消', 'registration_id': registration_id})
