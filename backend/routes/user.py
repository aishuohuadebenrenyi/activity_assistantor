from flask import Blueprint, request, jsonify
from ..models import db, User

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
def get_profile():
    # Mock user 1
    user = User.query.get(1) 
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict())

@user_bp.route('/profile', methods=['PUT'])
def update_profile():
    user = User.query.get(1) # Mock
    data = request.get_json()
    
    if 'username' in data: user.username = data['username']
    if 'bio' in data: user.bio = data['bio']
    if 'avatar_url' in data: user.avatar_url = data['avatar_url']
    
    db.session.commit()
    return jsonify(user.to_dict())
