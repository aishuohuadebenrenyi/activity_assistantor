from flask import Blueprint, request, jsonify
from ..models import db, Registration, CheckinRecord, Activity

participant_bp = Blueprint('participant', __name__)

@participant_bp.route('/<int:activity_id>/participants', methods=['GET'])
def get_participants(activity_id):
    # Ensure activity exists
    Activity.query.get_or_404(activity_id)
    
    registrations = Registration.query.filter_by(activity_id=activity_id).all()
    
    result = []
    for reg in registrations:
        item = reg.to_dict()
        # Add checkin info if exists
        checkin = CheckinRecord.query.filter_by(registration_id=reg.id).first()
        if checkin:
            item['checkin_time'] = checkin.checkin_time.isoformat()
            item['checked_in'] = True
        else:
            item['checked_in'] = False
        result.append(item)
        
    return jsonify(result)

@participant_bp.route('/<int:activity_id>/register', methods=['POST'])
def register(activity_id):
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    
    if not name or not phone:
        return jsonify({'error': 'Missing name or phone'}), 400
        
    # Check duplicate
    existing = Registration.query.filter_by(activity_id=activity_id, phone=phone).first()
    if existing:
        return jsonify({'error': 'Already registered'}), 400
        
    reg = Registration(activity_id=activity_id, name=name, phone=phone)
    db.session.add(reg)
    db.session.commit()
    
    return jsonify(reg.to_dict()), 201

@participant_bp.route('/<int:activity_id>/checkin', methods=['POST'])
def checkin(activity_id):
    data = request.get_json()
    registration_id = data.get('registration_id')
    
    reg = Registration.query.get_or_404(registration_id)
    if reg.activity_id != activity_id:
        return jsonify({'error': 'Invalid registration for this activity'}), 400
        
    if CheckinRecord.query.filter_by(registration_id=registration_id).first():
         return jsonify({'error': 'Already checked in'}), 400
         
    record = CheckinRecord(
        registration_id=registration_id,
        activity_id=activity_id,
        device_info=data.get('device_info', 'unknown')
    )
    db.session.add(record)
    db.session.commit()
    
    return jsonify(record.to_dict())

@participant_bp.route('/<int:activity_id>/checkin/<int:record_id>', methods=['DELETE'])
def cancel_checkin(activity_id, record_id):
    record = CheckinRecord.query.get_or_404(record_id)
    if record.activity_id != activity_id:
        return jsonify({'error': 'Mismatch activity'}), 400
        
    db.session.delete(record)
    db.session.commit()
    return jsonify({'message': 'Checkin cancelled'})
