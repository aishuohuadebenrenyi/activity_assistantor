"""
活动相关 API。

路由前缀：/api/activities

覆盖能力：
- 活动列表/详情/创建/更新/删除；
- 分享（生成微信 URL Link 与小程序码数据）；
- 参与者票据（生成签到码）；
- 组织者核销签到；
- 活动举报。

说明：
- 写接口统一接入幂等（Idempotency-Key），用于弱网重试/离线队列重放；
- 多数接口仍沿用历史的 `{error: ...}` 形式错误响应，需与前端兼容。
"""

from flask import Blueprint, request, jsonify, g
from ..models import db, Activity, User, Registration, CheckinRecord, Report
from ..services.wechat_service import WeChatService
from ..utils.auth import auth_required
from ..utils.idempotency import idempotent
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('/', methods=['GET'])
def get_activities():
    """
    获取活动列表（支持分页）
    ---
    tags:
      - 活动
    summary: 获取活动列表
    description: 支持按状态筛选、关键词搜索和分页
    parameters:
      - name: status
        in: query
        type: string
        enum: [all, ongoing, upcoming, ended]
        default: all
        description: 活动状态筛选
      - name: search
        in: query
        type: string
        description: 按活动名称或地点模糊搜索
      - name: page
        in: query
        type: integer
        default: 1
        description: 页码
      - name: page_size
        in: query
        type: integer
        default: 20
        maximum: 100
        description: 每页数量
    responses:
      200:
        description: 成功获取活动列表
        schema:
          type: object
          properties:
            activities:
              type: array
              items:
                $ref: '#/components/schemas/Activity'
            total:
              type: integer
              description: 总数
            page:
              type: integer
              description: 当前页
            page_size:
              type: integer
              description: 每页数量
            has_more:
              type: boolean
              description: 是否有更多
    """
    logger.info("[ACTIVITY] 获取活动列表请求")
    
    status = request.args.get('status')
    search = request.args.get('search')
    page = int(request.args.get('page', 1))
    page_size = min(int(request.args.get('page_size', 20)), 100)
    
    query = Activity.query
    
    if status and status != 'all':
        query = query.filter_by(status=status)
        logger.debug(f"[ACTIVITY] 筛选状态: {status}")
        
    if search:
        query = query.filter(Activity.name.contains(search) | Activity.location.contains(search))
        logger.debug(f"[ACTIVITY] 搜索关键词: {search}")
    
    total = query.count()
    
    activities = query.order_by(Activity.start_time.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()
    
    has_more = (page * page_size) < total
    
    logger.info(f"[ACTIVITY] 返回 {len(activities)} 个活动，共 {total} 个，第 {page} 页")
    
    return jsonify({
        'activities': [a.to_dict(include_registrations=False) for a in activities],
        'total': total,
        'page': page,
        'page_size': page_size,
        'has_more': has_more
    })

@activity_bp.route('/', methods=['POST'])
@auth_required
@idempotent
def create_activity():
    """
    创建活动
    ---
    tags:
      - 活动
    summary: 创建新活动
    description: |
      创建活动需要登录。
      创建前会对活动名称、描述、地点进行微信内容安全校验。
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - date
            - time
          properties:
            name:
              type: string
              description: 活动名称
              example: 2024年度技术分享会
            type:
              type: string
              description: 活动类型
              default: 其他
              example: business
            date:
              type: string
              format: date
              description: 活动日期
              example: "2024-03-25"
            time:
              type: string
              description: 活动时间
              example: "14:00"
            end_date:
              type: string
              format: date
              description: 结束日期
              example: "2024-03-25"
            end_time:
              type: string
              description: 结束时间
              example: "16:00"
            location:
              type: string
              description: 活动地点
              example: 北京市朝阳区xxx大厦
            description:
              type: string
              description: 活动介绍
              example: 本次分享会将探讨最新技术趋势
            capacity:
              type: integer
              description: 人数限制，0表示不限
              default: 0
              example: 100
            host_phone:
              type: string
              description: 主办方电话
              example: "13800138000"
            host_wechat:
              type: string
              description: 主办方微信
              example: wechat_id
            show_phone:
              type: boolean
              description: 是否公开电话
              default: false
            show_wechat:
              type: boolean
              description: 是否公开微信
              default: false
    responses:
      201:
        description: 创建成功
        schema:
          $ref: '#/components/schemas/Activity'
      400:
        description: 参数错误或内容违规
        schema:
          $ref: '#/components/schemas/ErrorResponse'
      401:
        $ref: '#/components/responses/UnauthorizedError'
    """
    data = request.get_json()
    user = request.user
    
    # 微信内容安全校验 - 扩展校验范围
    content_to_check = data['name']
    if data.get('description'):
        content_to_check += " " + data['description']
    if data.get('location'):
        content_to_check += " " + data['location']
    if data.get('host_wechat'):
        content_to_check += " " + data['host_wechat']
    
    if not WeChatService.check_content_security(content_to_check):
        return jsonify({'error': '内容包含违规信息'}), 400
    
    try:
        start_time = datetime.fromisoformat(data['date'] + 'T' + data['time'])
        
        # 处理结束时间
        end_time = None
        if data.get('end_date') and data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_date'] + 'T' + data['end_time'])
        elif data.get('duration_hours'):
            from datetime import timedelta
            end_time = start_time + timedelta(hours=int(data['duration_hours']))
        
        new_activity = Activity(
            user_id=user.id,
            name=data['name'],
            type=data.get('type', '其他'),
            start_time=start_time,
            end_time=end_time,
            location=data.get('location'),
            description=data.get('description'),
            capacity=int(data.get('capacity', 0)),
            host_phone=data.get('host_phone'),
            host_wechat=data.get('host_wechat'),
            show_phone=data.get('show_phone', False),
            show_wechat=data.get('show_wechat', False)
        )
        db.session.add(new_activity)
        db.session.commit()
        return jsonify(new_activity.to_dict(is_organizer=True)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@activity_bp.route('/<int:id>', methods=['GET'])
def get_activity(id):
    """
    获取活动详情。

    业务规则（敏感信息保护）：
    - 若请求方是该活动组织者，则返回报名手机号明文；
    - 否则返回脱敏手机号（mask_registrations=True）。
    - 联系方式仅对已报名用户和组织者可见。
    - 每次查看活动详情，浏览量 +1。

    判断方式：
    - 若请求携带 Authorization，则尝试解析 JWT；
    - JWT 解析失败或未携带，则视为非组织者。
    """
    activity = Activity.query.get_or_404(id)
    
    activity.views_count += 1
    db.session.commit()
    
    auth_header = request.headers.get('Authorization')
    is_organizer = False
    is_registered = False
    user_id = None
    
    if auth_header:
        try:
            from flask import current_app
            import jwt
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
            if user_id == activity.user_id:
                is_organizer = True
        except:
            pass
    
    if user_id and not is_organizer:
        user = User.query.get(user_id)
        if user and user.phone:
            registration = Registration.query.filter_by(
                activity_id=id, 
                phone=user.phone
            ).first()
            if registration:
                is_registered = True
            
    return jsonify(activity.to_dict(
        mask_registrations=not is_organizer,
        show_contact=is_registered,
        is_organizer=is_organizer
    ))

@activity_bp.route('/<int:id>', methods=['PUT'])
@auth_required
@idempotent
def update_activity(id):
    """
    更新活动（需要登录，且仅组织者可更新）。

    Body（JSON）：支持部分字段更新：
    - name/location/description/type/capacity
    - date/time 同时提供时更新 start_time
    - end_date/end_time 或 duration_hours 更新 end_time
    - host_phone/host_wechat/show_phone/show_wechat 联系方式相关

    业务规则：
    - name/description/location/host_wechat 更新会触发微信内容安全校验；
    - 非组织者返回 403。
    """
    activity = Activity.query.get_or_404(id)
    
    if activity.user_id != request.user.id:
        return jsonify({'error': '没有权限修改此活动'}), 403
        
    data = request.get_json()
    
    # 收集需要校验的内容
    content_to_check = ""
    if 'name' in data:
        content_to_check += data['name'] + " "
    if 'description' in data:
        content_to_check += data['description'] + " "
    if 'location' in data:
        content_to_check += data['location'] + " "
    if 'host_wechat' in data:
        content_to_check += data['host_wechat'] + " "
    
    # 统一进行内容安全校验
    if content_to_check.strip():
        if not WeChatService.check_content_security(content_to_check):
            return jsonify({'error': '内容包含违规信息'}), 400
    
    if 'name' in data: 
        activity.name = data['name']
        
    if 'location' in data: activity.location = data['location']
    
    if 'description' in data: 
        activity.description = data['description']
        
    if 'type' in data: activity.type = data['type']
    if 'capacity' in data: activity.capacity = int(data['capacity'])
    
    if 'host_phone' in data: activity.host_phone = data['host_phone'] or None
    if 'host_wechat' in data: activity.host_wechat = data['host_wechat'] or None
    if 'show_phone' in data: activity.show_phone = bool(data['show_phone'])
    if 'show_wechat' in data: activity.show_wechat = bool(data['show_wechat'])
    
    if 'date' in data and 'time' in data:
        try:
            activity.start_time = datetime.fromisoformat(data['date'] + 'T' + data['time'])
        except ValueError:
            return jsonify({'error': '日期格式错误'}), 400
    
    # 更新结束时间
    if 'end_date' in data and 'end_time' in data:
        try:
            activity.end_time = datetime.fromisoformat(data['end_date'] + 'T' + data['end_time'])
        except ValueError:
            return jsonify({'error': '结束日期格式错误'}), 400
    elif 'duration_hours' in data:
        from datetime import timedelta
        activity.end_time = activity.start_time + timedelta(hours=int(data['duration_hours']))
            
    db.session.commit()
    return jsonify(activity.to_dict(is_organizer=True))

@activity_bp.route('/<int:id>/share', methods=['GET'])
def share_activity(id):
    """
    获取活动分享信息（微信 URL Link 与小程序码）。

    返回：
    - url_link: 适用于微信生态的 URL Link（由后端生成）
    - qrcode_data: 小程序码二进制/数据（由后端生成，前端决定如何展示）
    - activity_name/activity_info: 便于前端生成分享卡片
    """
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
    """
    获取"我的票据"（需要登录）。

    业务规则：
    - 优先通过 user_id 匹配报名记录；
    - 若 user_id 未匹配，则通过 phone 匹配（兼容旧数据）；
    - 若用户未报名则返回 404。

    返回：
    - registration: 报名信息
    - ticket_code: Base64 编码的签到码（格式 CHECKIN:<activity_id>:<registration_id>:<timestamp>:<signature>）
    - qr_code_image: Base64 编码的二维码图片（PNG格式）
    - activity: 活动信息（包含主办方联系方式）
    """
    from ..services.qrcode_service import generate_checkin_qrcode
    
    user = request.user
    activity = Activity.query.get_or_404(id)
    
    # 优先通过 user_id 查找报名记录
    registration = Registration.query.filter_by(activity_id=id, user_id=user.id).first()
    
    # 兼容旧数据：通过 phone 匹配
    if not registration and user.phone:
        registration = Registration.query.filter_by(activity_id=id, phone=user.phone).first()
    
    if not registration:
        return jsonify({'error': '您尚未报名此活动'}), 404

    import time
    timestamp = int(time.time())
    
    b64_code, qr_base64 = generate_checkin_qrcode(id, registration.id, timestamp)
    
    return jsonify({
        'registration': registration.to_dict(),
        'ticket_code': b64_code,
        'qr_code_image': qr_base64,
        'activity': activity.to_dict(show_contact=True, is_organizer=False)
    })

@activity_bp.route('/<int:id>/checkin', methods=['POST'])
@auth_required
@idempotent
def checkin_user(id):
    """
    核销签到（需要登录，且仅组织者可核销）。

    Body（JSON）二选一：
    - qr_data: Base64 签到码（由 /my-ticket 生成）
    - registration_id: 直接传报名记录 ID（方便无扫码能力的兜底）

    返回：
    - 200: 签到成功/已签到提示；
    - 400/404/403: 参数缺失/无权限/记录不存在等。
    """
    from ..services.qrcode_service import verify_signature
    
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
            
            if len(parts) < 4 or parts[0] != 'CHECKIN':
                 return jsonify({'error': '无效的二维码'}), 400
            
            aid = int(parts[1])
            rid = int(parts[2])
            timestamp = int(parts[3])
            
            if aid != id:
                return jsonify({'error': '非本活动的签到码'}), 400
            
            if len(parts) >= 5:
                signature = parts[4]
                valid, error_msg = verify_signature(aid, rid, timestamp, signature)
                if not valid:
                    return jsonify({'error': error_msg}), 400
        else:
            rid = registration_id

        registration = Registration.query.get(rid)
        if not registration or registration.activity_id != id:
            return jsonify({'error': '报名记录不存在'}), 404
            
        if registration.checkin_record:
            return jsonify({'message': '该用户已签到', 'user': registration.name, 'already_checked': True, 'registration_id': registration.id})
            
        new_record = CheckinRecord(
            registration_id=rid,
            activity_id=id,
            checkin_time=datetime.utcnow()
        )
        db.session.add(new_record)
        db.session.commit()
        
        return jsonify({'message': '签到成功', 'user': registration.name, 'already_checked': False, 'registration_id': registration.id})
        
    except Exception as e:
        return jsonify({'error': f'签到失败: {str(e)}'}), 400

@activity_bp.route('/<int:id>/report', methods=['POST'])
@auth_required
@idempotent
def report_activity(id):
    """
    举报活动（需要登录）。

    Body（JSON）：
    - reason: 举报原因（必填）
    - detail: 详情描述（可选）

    返回：
    - 200: 受理成功，返回 report_id；
    - 400: 缺少 reason。
    """
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
@idempotent
def delete_activity(id):
    """
    删除活动（需要登录，且仅组织者可删除）。

    数据影响：
    - Activity 删除会级联删除 registrations/checkin_records（见 models.py 的 cascade 配置）。

    返回：
    - 200: 删除成功；
    - 403: 非组织者无权限删除。
    """
    activity = Activity.query.get_or_404(id)
    
    if activity.user_id != request.user.id:
        return jsonify({'error': '没有权限删除此活动'}), 403
        
    db.session.delete(activity)
    db.session.commit()
    return jsonify({'message': 'Activity deleted'})
