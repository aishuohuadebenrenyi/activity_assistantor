from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    username = db.Column(db.String(64), default='用户')
    avatar_url = db.Column(db.String(255))
    bio = db.Column(db.Text)
    is_certified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    activities = db.relationship('Activity', backref='organizer', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'username': self.username,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'is_certified': self.is_certified,
            'created_at': self.created_at.isoformat()
        }

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(50))
    start_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    capacity = db.Column(db.Integer, default=0)  # 0 means unlimited
    status = db.Column(db.String(20), default='upcoming')  # upcoming, ongoing, ended
    views_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    registrations = db.relationship('Registration', backref='activity', lazy='dynamic', cascade='all, delete-orphan')
    checkin_records = db.relationship('CheckinRecord', backref='activity', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        registrations_list = [r.to_dict() for r in self.registrations]
        checkins_list = [c.to_dict() for c in self.checkin_records]
        
        return {
            'id': self.id,
            'organizer_id': self.user_id,
            'name': self.name,
            'type': self.type,
            'start_time': self.start_time.isoformat(),
            'location': self.location,
            'description': self.description,
            'capacity': self.capacity,
            'status': self.status,
            'views_count': self.views_count,
            'created_at': self.created_at.isoformat(),
            'registrations': registrations_list,
            'checkin_records': checkins_list
        }

class Registration(db.Model):
    __tablename__ = 'registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    
    # For this simple version, we might just store name/phone if users don't need to be registered users to sign up
    # Or link to User if they are logged in. Let's assume standalone registration for now as per requirements analysis.
    name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    checkin_record = db.relationship('CheckinRecord', backref='registration', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'activity_id': self.activity_id,
            'name': self.name,
            'phone': self.phone,
            'created_at': self.created_at.isoformat(),
            'checked_in': self.checkin_record is not None
        }

class CheckinRecord(db.Model):
    __tablename__ = 'checkin_records'
    
    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), nullable=False, unique=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    
    checkin_time = db.Column(db.DateTime, default=datetime.utcnow)
    device_info = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'registration_id': self.registration_id,
            'activity_id': self.activity_id,
            'checkin_time': self.checkin_time.isoformat()
        }
