from flask import Blueprint, request, jsonify, g
from ..models import db, Activity, User, Registration, CheckinRecord, Report
from ..services.wechat_service import WeChatService
from ..utils.auth import auth_required
from datetime import datetime

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('/', methods=['GET'])
def get_activities():
    status = request.args.get('status')
    search = request.args.get('search')
    
    query = Activity.query
    
    if status and status != 'all':
        query = query.filter_by(status=status)
        
    if search:
        query = query.filter(Activity.name.contains(search) | Activity.location.contains(search))
        
    activities = query.order_by(Activity.start_time.desc()).all()
    # 列表页不返回报名详情，减少流量消耗且更安全
    return jsonify([a.to_dict(include_registrations=False) for a in activities])

@activity_bp.route('/', methods=['POST'])
@auth_required
def create_activity():
    data = request.get_json()
    user = request.user
    
    # 微信内容安全校验
    if not WeChatService.check_content_security(data['name'] + " " + data.get('description', '')):
        return jsonify({'error': '内容包含违规信息'}), 400
    
    try:
        new_activity = Activity(
            user_id=user.id,
            name=data['name'],
            type=data.get('type', '其他'),
            start_time=datetime.fromisoformat(data['date'] + 'T' + data['time']),
            location=data.get('location'),
            description=data.get('description'),
            capacity=int(data.get('capacity', 0))
        )
        db.session.add(new_activity)
        db.session.commit()
        return jsonify(new_activity.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@activity_bp.route('/<int:id>', methods=['GET'])
def get_activity(id):
    activity = Activity.query.get_or_404(id)
    
    # 尝试获取当前用户以判断是否是组织者
    auth_header = request.headers.get('Authorization')
    is_organizer = False
    if auth_header:
        try:
            from flask import current_app
            import jwt
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            if payload['user_id'] == activity.user_id:
                is_organizer = True
        except:
            pass
            
    # 如果不是组织者，脱敏显示报名人员手机号
    return jsonify(activity.to_dict(mask_registrations=not is_organizer))

@activity_bp.route('/<int:id>', methods=['PUT'])
@auth_required
def update_activity(id):
    activity = Activity.query.get_or_404(id)
    
    # Permission Check
    if activity.user_id != request.user.id:
        return jsonify({'error': '没有权限修改此活动'}), 403
        
    data = request.get_json()
    
    if 'name' in data: 
        if not WeChatService.check_content_security(data['name']):
            return jsonify({'error': '活动名称包含违规信息'}), 400
        activity.name = data['name']
        
    if 'location' in data: activity.location = data['location']
    
    if 'description' in data: 
        if not WeChatService.check_content_security(data['description']):
            return jsonify({'error': '活动描述包含违规信息'}), 400
        activity.description = data['description']
        
    if 'type' in data: activity.type = data['type']
    if 'capacity' in data: activity.capacity = int(data['capacity'])
    
    # Handle date/time update
    if 'date' in data and 'time' in data:
        try:
            activity.start_time = datetime.fromisoformat(data['date'] + 'T' + data['time'])
        except ValueError:
            return jsonify({'error': '日期格式错误'}), 400
            
    db.session.commit()
    return jsonify(activity.to_dict())

@activity_bp.route('/<int:id>/share', methods=['GET'])
def share_activity(id):
    activity = Activity.query.get_or_404(id)
    
    url_link = WeChatService.generate_url_link(
        path="pages/activity/detail/detail",
        query=f"id={id}"
    )
    
    qrcode_data = WeChatService.get_unlimited_qrcode(
        scene=f"id={id}",
        page="pages/activity/detail/detail" 
    )
    
    return jsonify({
        "url_link": url_link,
        "qrcode_data": qrcode_data,
        "activity_name": activity.name,
        "activity_info": activity.to_dict()
    })

@activity_bp.route('/<int:id>/my-ticket', methods=['GET'])
@auth_required
def get_my_ticket(id):
    user = request.user
    activity = Activity.query.get_or_404(id)
    
    # Find registration by phone (since Registration model is simple)
    # In a real app, Registration would have a user_id.
    registration = Registration.query.filter_by(activity_id=id, phone=user.phone).first()
    
    if not registration:
        return jsonify({'error': '您尚未报名此活动'}), 404

    # Generate check-in code
    import base64
    import time
    
    code_content = f"CHECKIN:{id}:{registration.id}:{int(time.time())}"
    b64_code = base64.b64encode(code_content.encode('utf-8')).decode('utf-8')
    
    return jsonify({
        'registration': registration.to_dict(),
        'ticket_code': b64_code,
        'activity': activity.to_dict()
    })

@activity_bp.route('/<int:id>/checkin', methods=['POST'])
@auth_required
def checkin_user(id):
    # Only organizer can checkin others
    activity = Activity.query.get_or_404(id)
    if activity.user_id != request.user.id:
        return jsonify({'error': '只有活动组织者可以进行签到操作'}), 403
        
    data = request.get_json()
    qr_data = data.get('qr_data')
    registration_id = data.get('registration_id')
    
    if not qr_data and not registration_id:
        return jsonify({'error': '缺少签到数据'}), 400
        
    try:
        rid = None
        if qr_data:
            import base64
            decoded = base64.b64decode(qr_data).decode('utf-8')
            parts = decoded.split(':')
            
            if len(parts) != 4 or parts[0] != 'CHECKIN':
                 return jsonify({'error': '无效的二维码'}), 400
                 
            aid = int(parts[1])
            rid = int(parts[2])
            
            if aid != id:
                return jsonify({'error': '非本活动的签到码'}), 400
        else:
            rid = registration_id

        registration = Registration.query.get(rid)
        if not registration or registration.activity_id != id:
            return jsonify({'error': '报名记录不存在'}), 404
            
        if registration.checkin_record:
            return jsonify({'message': '该用户已签到', 'user': registration.name, 'already_checked': True})
            
        new_record = CheckinRecord(
            registration_id=rid,
            activity_id=id,
            checkin_time=datetime.utcnow()
        )
        db.session.add(new_record)
        db.session.commit()
        
        return jsonify({'message': '签到成功', 'user': registration.name, 'already_checked': False})
        
    except Exception as e:
        return jsonify({'error': f'签到失败: {str(e)}'}), 400

@activity_bp.route('/<int:id>/report', methods=['POST'])
@auth_required
def report_activity(id):
    activity = Activity.query.get_or_404(id)
    data = request.get_json()
    reason = data.get('reason')
    user = request.user
    
    if not reason:
        return jsonify({'error': '缺少举报原因'}), 400
        
    new_report = Report(
        activity_id=id,
        user_id=user.id,
        reason=reason,
        detail=data.get('detail', '')
    )
    db.session.add(new_report)
    db.session.commit()
    
    return jsonify({'message': '举报已收到，我们会尽快处理', 'report_id': new_report.id})

@activity_bp.route('/<int:id>', methods=['DELETE'])
@auth_required
def delete_activity(id):
    activity = Activity.query.get_or_404(id)
    
    if activity.user_id != request.user.id:
        return jsonify({'error': '没有权限删除此活动'}), 403
        
    db.session.delete(activity)
    db.session.commit()
    return jsonify({'message': 'Activity deleted'})
