from flask import Blueprint, request, jsonify
from ..models import db, Activity, User
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

@activity_bp.route('/<int:id>', methods=['DELETE'])
def delete_activity(id):
    activity = Activity.query.get_or_404(id)
    db.session.delete(activity)
    db.session.commit()
    return jsonify({'message': 'Activity deleted'})
