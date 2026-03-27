from flask import Blueprint, request, jsonify, g
from models import db, EventLog
from datetime import datetime
import json
import hashlib
from functools import wraps

analytics_bp = Blueprint('analytics', __name__)


def validate_app_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        app_key = request.headers.get('X-App-Key')
        if not app_key:
            return jsonify({'error': 'Missing app key'}), 401
        
        expected_key = 'zentro_analytics_key'
        if app_key != expected_key:
            return jsonify({'error': 'Invalid app key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def mask_sensitive_data(data):
    SENSITIVE_KEYS = ['phone', 'mobile', 'email', 'password', 'token', 'secret', 'id_card']
    
    if not isinstance(data, dict):
        return data
    
    masked = dict(data)
    for key in list(masked.keys()):
        lower_key = key.lower()
        if any(s in lower_key for s in SENSITIVE_KEYS):
            value = masked[key]
            if isinstance(value, str):
                if 'phone' in lower_key or 'mobile' in lower_key:
                    if len(value) >= 7:
                        masked[key] = value[:3] + '****' + value[-4:]
                elif 'email' in lower_key:
                    if '@' in value:
                        parts = value.split('@')
                        masked[key] = parts[0][:2] + '***@' + parts[1]
                else:
                    masked[key] = '******'
    
    return masked


@analytics_bp.route('/events', methods=['POST'])
def receive_events():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    events = data.get('events', [])
    device_info = data.get('device_info', {})
    
    if not events:
        return jsonify({'message': 'No events to process', 'count': 0}), 200
    
    if len(events) > 100:
        return jsonify({'error': 'Too many events in single request (max 100)'}), 400
    
    event_records = []
    processed_count = 0
    skipped_count = 0
    
    for event in events:
        try:
            event_id = event.get('event_id')
            event_name = event.get('event_name')
            timestamp = event.get('timestamp')
            user_id = event.get('user_id')
            device_id = event.get('device_id', '')
            session_id = event.get('session_id', '')
            platform = event.get('platform', 'unknown')
            app_version = event.get('app_version', '')
            properties = event.get('properties', {})
            
            if not event_name:
                skipped_count += 1
                continue
            
            masked_properties = mask_sensitive_data(properties)
            
            record = EventLog(
                event_name=event_name,
                user_id=int(user_id) if user_id else None,
                org_id=None,
                platform=platform,
                app_version=app_version,
                device_id=device_id,
                request_id=session_id,
                properties=json.dumps(masked_properties, ensure_ascii=False),
                created_at=datetime.utcfromtimestamp(timestamp / 1000) if timestamp else datetime.utcnow()
            )
            event_records.append(record)
            processed_count += 1
            
        except Exception as e:
            skipped_count += 1
            continue
    
    if event_records:
        try:
            db.session.bulk_save_objects(event_records)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Events received',
        'processed': processed_count,
        'skipped': skipped_count,
        'total': len(events)
    }), 200


@analytics_bp.route('/events/batch', methods=['POST'])
def receive_events_batch():
    return receive_events()


@analytics_bp.route('/events/query', methods=['POST'])
def query_events():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    event_names = data.get('event_names', [])
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    user_id = data.get('user_id')
    platform = data.get('platform')
    limit = data.get('limit', 100)
    offset = data.get('offset', 0)
    
    query = EventLog.query
    
    if event_names:
        query = query.filter(EventLog.event_name.in_(event_names))
    
    if start_time:
        if isinstance(start_time, (int, float)):
            start_dt = datetime.utcfromtimestamp(start_time / 1000)
        else:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        query = query.filter(EventLog.created_at >= start_dt)
    
    if end_time:
        if isinstance(end_time, (int, float)):
            end_dt = datetime.utcfromtimestamp(end_time / 1000)
        else:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        query = query.filter(EventLog.created_at <= end_dt)
    
    if user_id:
        query = query.filter(EventLog.user_id == user_id)
    
    if platform:
        query = query.filter(EventLog.platform == platform)
    
    total = query.count()
    
    events = query.order_by(EventLog.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for event in events:
        props = {}
        if event.properties:
            try:
                props = json.loads(event.properties)
            except:
                pass
        
        result.append({
            'id': event.id,
            'event_name': event.event_name,
            'user_id': event.user_id,
            'platform': event.platform,
            'app_version': event.app_version,
            'device_id': event.device_id,
            'session_id': event.request_id,
            'properties': props,
            'created_at': event.created_at.isoformat()
        })
    
    return jsonify({
        'events': result,
        'total': total,
        'limit': limit,
        'offset': offset
    }), 200


@analytics_bp.route('/stats/daily', methods=['GET'])
def get_daily_stats():
    from sqlalchemy import func
    
    date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return jsonify({'error': 'Invalid date format, use YYYY-MM-DD'}), 400
    
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())
    
    event_counts = db.session.query(
        EventLog.event_name,
        func.count(EventLog.id).label('count')
    ).filter(
        EventLog.created_at >= start_dt,
        EventLog.created_at <= end_dt
    ).group_by(EventLog.event_name).all()
    
    dau = db.session.query(
        func.count(func.distinct(EventLog.user_id)).label('dau')
    ).filter(
        EventLog.created_at >= start_dt,
        EventLog.created_at <= end_dt,
        EventLog.user_id.isnot(None)
    ).scalar()
    
    device_count = db.session.query(
        func.count(func.distinct(EventLog.device_id)).label('devices')
    ).filter(
        EventLog.created_at >= start_dt,
        EventLog.created_at <= end_dt
    ).scalar()
    
    platform_dist = db.session.query(
        EventLog.platform,
        func.count(EventLog.id).label('count')
    ).filter(
        EventLog.created_at >= start_dt,
        EventLog.created_at <= end_dt
    ).group_by(EventLog.platform).all()
    
    return jsonify({
        'date': date_str,
        'dau': dau or 0,
        'device_count': device_count or 0,
        'event_counts': {name: count for name, count in event_counts},
        'platform_distribution': {platform: count for platform, count in platform_dist}
    }), 200


@analytics_bp.route('/stats/funnel', methods=['POST'])
def get_funnel_stats():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    steps = data.get('steps', [])
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not steps or len(steps) < 2:
        return jsonify({'error': 'At least 2 steps required'}), 400
    
    from sqlalchemy import func
    
    start_dt = None
    end_dt = None
    
    if start_time:
        if isinstance(start_time, (int, float)):
            start_dt = datetime.utcfromtimestamp(start_time / 1000)
        else:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    
    if end_time:
        if isinstance(end_time, (int, float)):
            end_dt = datetime.utcfromtimestamp(end_time / 1000)
        else:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    funnel_result = []
    previous_count = None
    
    for i, step in enumerate(steps):
        event_name = step.get('event_name')
        
        query = db.session.query(
            func.count(func.distinct(EventLog.user_id)).label('unique_users'),
            func.count(EventLog.id).label('total_events')
        ).filter(
            EventLog.event_name == event_name
        )
        
        if start_dt:
            query = query.filter(EventLog.created_at >= start_dt)
        if end_dt:
            query = query.filter(EventLog.created_at <= end_dt)
        
        result = query.first()
        
        unique_users = result.unique_users or 0
        total_events = result.total_events or 0
        
        conversion_rate = None
        if previous_count is not None and previous_count > 0:
            conversion_rate = round(unique_users / previous_count * 100, 2)
        
        funnel_result.append({
            'step': i + 1,
            'event_name': event_name,
            'unique_users': unique_users,
            'total_events': total_events,
            'conversion_rate': conversion_rate
        })
        
        previous_count = unique_users
    
    return jsonify({
        'funnel': funnel_result,
        'total_steps': len(steps)
    }), 200


@analytics_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'service': 'analytics',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
