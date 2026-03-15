from flask import Blueprint, request, jsonify, current_app
from ..models import db, Registration, CheckinRecord, Activity
from ..utils.auth import auth_required
import csv
import io

participant_bp = Blueprint('participant', __name__)

@participant_bp.route('/<int:activity_id>/participants', methods=['GET'])
@auth_required
def get_participants(activity_id):
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
def register(activity_id):
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
def export_participants(activity_id):
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
