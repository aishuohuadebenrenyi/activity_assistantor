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
    # Ensure activity exists and user is organizer
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
    - 以 (activity_id, phone) 判断重复报名；重复则返回错误；
    - 当前 Registration 模型未强制绑定 user_id，因此允许“代报名”或未实名场景。

    返回：
    - 201: 报名成功，返回 Registration；
    - 400: 参数缺失或已报名。
    """
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    
    if not name or not phone:
        return jsonify({'error': 'Missing name or phone'}), 400
        
    # Check duplicate
    existing = Registration.query.filter_by(activity_id=activity_id, phone=phone).first()
    if existing:
        return jsonify({'error': '您已经报名过此活动'}), 400
        
    reg = Registration(activity_id=activity_id, name=name, phone=phone)
    db.session.add(reg)
    db.session.commit()
    
    return jsonify(reg.to_dict()), 201

@participant_bp.route('/<int:activity_id>/export', methods=['POST'])
@auth_required
@idempotent
def export_participants(activity_id):
    """
    导出报名名单（仅组织者可访问）。

    Body（JSON）：
    - email: 接收导出的邮箱（必填）

    当前实现说明：
    - 以 CSV 格式生成内容；
    - 发送邮件逻辑为 Mock（仅打印），用于演示“异步导出”交互；
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
        
    # Generate CSV
    registrations = Registration.query.filter_by(activity_id=activity_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '姓名', '电话', '报名时间', '是否签到'])
    
    for reg in registrations:
        checked_in = "是" if reg.checkin_record else "否"
        writer.writerow([reg.id, reg.name, reg.phone, reg.created_at.isoformat(), checked_in])
    
    csv_content = output.getvalue()
    
    # Mock Email Sending
    print(f"DEBUG: [EMAIL SERVICE] Sending participant list of '{activity.name}' to {email}")
    print(f"DEBUG: CSV Content:\n{csv_content}")
    
    return jsonify({'message': '导出请求已接收，报名名单将在3个工作日内发送至您的邮箱'}), 202
