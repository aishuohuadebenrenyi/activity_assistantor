from flask import Blueprint, request, jsonify
from ..models import db, Activity, User
from ..services.wechat_service import WeChatService
from datetime import datetime

activity_bp = Blueprint('activity', __name__)

# Helper to get user_id from token (Mock for now, should use decorator)
def get_current_user_id():
    # In real implementation, parse 'Authorization' header
    # auth_header = request.headers.get('Authorization')
    # ... decode jwt ...
    return 1 # Mock User ID 1

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
    return jsonify([a.to_dict() for a in activities])

@activity_bp.route('/', methods=['POST'])
def create_activity():
    data = request.get_json()
    user_id = get_current_user_id()
    
    # 微信内容安全校验 (Mock)
    # 真实场景需调用微信 security.msgSecCheck 接口
    # if not check_content_security(data['name'], data.get('description', '')):
    #     return jsonify({'error': '内容包含违规信息'}), 400
    
    try:
        new_activity = Activity(
            user_id=user_id,
            name=data['name'],
            type=data.get('type', '其他'),
            start_time=datetime.fromisoformat(data['date'] + 'T' + data['time']), # Assuming simple ISO format
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
    return jsonify(activity.to_dict())

@activity_bp.route('/<int:id>', methods=['PUT'])
def update_activity(id):
    activity = Activity.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data: activity.name = data['name']
    if 'location' in data: activity.location = data['location']
    if 'description' in data: activity.description = data['description']
    # Add other fields as needed
    
    db.session.commit()
    return jsonify(activity.to_dict())

@activity_bp.route('/<int:id>/share', methods=['GET'])
def share_activity(id):
    activity = Activity.query.get_or_404(id)
    
    # 1. Generate URL Link (https://wxaurl.cn/...)
    # Path: Mini Program Page Path
    # Query: Parameters
    url_link = WeChatService.generate_url_link(
        path="pages/activity/detail/detail",
        query=f"id={id}"
    )
    
    # 2. Generate QRCode (Unlimited)
    # Scene: id=123 (Max 32 chars)
    # Page: Must be released page
    qrcode_data = WeChatService.get_unlimited_qrcode(
        scene=f"id={id}",
        page="pages/activity/detail/detail" 
    )
    
    return jsonify({
        "url_link": url_link,
        "qrcode_data": qrcode_data, # Base64 string or URL
        "activity_name": activity.name,
        "activity_info": activity.to_dict()
    })

@activity_bp.route('/<int:id>/my-ticket', methods=['GET'])
def get_my_ticket(id):
    user_id = get_current_user_id()
    # Find registration for this user and activity
    # In a real app, you'd query Registration where user_id matches.
    # Since Registration model currently stores 'name' and 'phone' but not direct user_id (it's a simplified model),
    # we might need to mock this or assume the user can be found by phone if we had user phone.
    # For this mock, we'll just return the first registration or a mock one if none exists.
    
    activity = Activity.query.get_or_404(id)
    from ..models import Registration
    registration = Registration.query.filter_by(activity_id=id).first() # MOCK: Get first one
    
    if not registration:
        # Create a mock registration for demo purposes if none exists
        if 'mock' in (request.args.get('mode') or ''):
            pass 
        else:
            # Create a temporary mock registration object for display if database is empty
            class MockReg:
                id = 999
                name = "测试用户"
                phone = "13800000000"
                checkin_record = None
                created_at = datetime.utcnow()
                def to_dict(self):
                    return {
                        'id': self.id,
                        'name': self.name,
                        'phone': self.phone,
                        'checked_in': False
                    }
            registration = MockReg()

    # Generate a simple check-in code
    # Format: "CHECKIN:activity_id:registration_id:timestamp"
    # Base64 encode for safety
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
def checkin_user(id):
    data = request.get_json()
    qr_data = data.get('qr_data')
    
    if not qr_data:
        return jsonify({'error': '缺少二维码数据'}), 400
        
    try:
        import base64
        decoded = base64.b64decode(qr_data).decode('utf-8')
        # Format: CHECKIN:activity_id:registration_id:timestamp
        parts = decoded.split(':')
        
        if len(parts) != 4 or parts[0] != 'CHECKIN':
             return jsonify({'error': '无效的二维码'}), 400
             
        aid = int(parts[1])
        rid = int(parts[2])
        
        if aid != id:
            return jsonify({'error': '非本活动的签到码'}), 400
            
        from ..models import Registration
        registration = Registration.query.get(rid)
        if not registration:
            return jsonify({'error': '报名记录不存在'}), 404
            
        if registration.checkin_record:
            return jsonify({'message': '该用户已签到', 'user': registration.name, 'already_checked': True})
            
        # Perform check-in
        from ..models import CheckinRecord
        new_record = CheckinRecord(
            registration_id=rid,
            activity_id=aid,
            checkin_time=datetime.utcnow()
        )
        db.session.add(new_record)
        db.session.commit()
        
        return jsonify({'message': '签到成功', 'user': registration.name, 'already_checked': False})
        
    except Exception as e:
        return jsonify({'error': f'签到失败: {str(e)}'}), 400

@activity_bp.route('/<int:id>', methods=['DELETE'])
def delete_activity(id):
    activity = Activity.query.get_or_404(id)
    db.session.delete(activity)
    db.session.commit()
    return jsonify({'message': 'Activity deleted'})
