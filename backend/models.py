from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """
    用户模型
    存储用户的基本信息，如手机号、昵称、头像等。
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    # 手机号，唯一标识，用于登录
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    # 用户昵称，默认为'用户'
    username = db.Column(db.String(64), default='用户')
    # 头像 URL
    avatar_url = db.Column(db.String(255))
    # 个人简介
    bio = db.Column(db.Text)
    # 是否实名认证
    is_certified = db.Column(db.Boolean, default=False)
    # 账户创建时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系：该用户发布的所有活动
    activities = db.relationship('Activity', backref='organizer', lazy='dynamic')

    def to_dict(self):
        """将对象转换为字典，便于 JSON 序列化"""
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
    """
    活动模型
    存储活动的核心信息，包括时间、地点、状态等。
    """
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    # 外键：关联到发布者（组织者）
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 活动名称
    name = db.Column(db.String(128), nullable=False)
    # 活动类型（如：会议、展览、运动等）
    type = db.Column(db.String(50))
    # 开始时间
    start_time = db.Column(db.DateTime, nullable=False)
    # 地点
    location = db.Column(db.String(255))
    # 详细描述
    description = db.Column(db.Text)
    # 人数限制，0 表示不限制
    capacity = db.Column(db.Integer, default=0) 
    # 状态：upcoming(即将开始), ongoing(进行中), ended(已结束)
    status = db.Column(db.String(20), default='upcoming') 
    # 浏览量统计
    views_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：活动的报名记录（级联删除）
    registrations = db.relationship('Registration', backref='activity', lazy='dynamic', cascade='all, delete-orphan')
    # 关系：活动的签到记录（级联删除）
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
    """
    报名模型
    记录用户报名参加某个活动的信息。
    """
    __tablename__ = 'registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    # 外键：关联活动
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    
    # 报名人姓名（简化版，暂不强制关联 User 表，方便未注册用户报名）
    name = db.Column(db.String(64), nullable=False)
    # 报名人电话
    phone = db.Column(db.String(20), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系：该报名的签到记录（一对一）
    checkin_record = db.relationship('CheckinRecord', backref='registration', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'activity_id': self.activity_id,
            'name': self.name,
            'phone': self.phone,
            'created_at': self.created_at.isoformat(),
            # 辅助字段：是否已签到
            'checked_in': self.checkin_record is not None
        }

class CheckinRecord(db.Model):
    """
    签到记录模型
    记录实际到场的签到信息。
    """
    __tablename__ = 'checkin_records'
    
    id = db.Column(db.Integer, primary_key=True)
    # 外键：关联报名记录（一个报名只能签到一次）
    registration_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), nullable=False, unique=True)
    # 外键：关联活动（冗余字段，方便查询）
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    
    # 签到时间
    checkin_time = db.Column(db.DateTime, default=datetime.utcnow)
    # 设备信息（可选，用于防作弊）
    device_info = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'registration_id': self.registration_id,
            'activity_id': self.activity_id,
            'checkin_time': self.checkin_time.isoformat()
        }
