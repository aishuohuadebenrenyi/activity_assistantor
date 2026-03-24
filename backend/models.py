from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

db = SQLAlchemy()

def mask_phone(phone):
    """
    手机号脱敏处理，如 13812345678 -> 138****5678。

    参数：
    - phone: 原始手机号字符串

    返回：
    - str: 脱敏后的手机号；输入为空或长度不足时原样返回。
    """
    if not phone or len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"

class User(db.Model):
    """
    用户模型
    存储用户的基本信息，如手机号、昵称、头像等。
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    # 手机号，唯一标识，用于登录
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    # 微信 OpenID
    openid = db.Column(db.String(128), unique=True, nullable=True, index=True)
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
    # 注销请求时间（冷静期开始时间）
    deletion_requested_at = db.Column(db.DateTime, nullable=True)
    # 账户状态：active(活跃), pending_deletion(注销中), deleted(已脱敏)
    status = db.Column(db.String(20), default='active')
    
    # 关系：该用户发布的所有活动
    activities = db.relationship('Activity', backref='organizer', lazy='dynamic')

    def to_dict(self, mask=False):
        """
        将用户对象转换为可 JSON 序列化的字典。

        参数：
        - mask: 是否对手机号做脱敏显示

        返回：
        - dict: 用户字段快照（不包含敏感密钥类字段）。
        """
        return {
            'id': self.id,
            'phone': mask_phone(self.phone) if mask else self.phone,
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
    
    # 主办方联系方式（可选填写）
    host_phone = db.Column(db.String(20), nullable=True)
    host_wechat = db.Column(db.String(64), nullable=True)
    show_phone = db.Column(db.Boolean, default=False)
    show_wechat = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：活动的报名记录（级联删除）
    registrations = db.relationship('Registration', backref='activity', lazy='dynamic', cascade='all, delete-orphan')
    # 关系：活动的签到记录（级联删除）
    checkin_records = db.relationship('CheckinRecord', backref='activity', lazy='dynamic', cascade='all, delete-orphan')

    def calculate_status(self):
        """
        根据当前时间动态计算活动状态。

        状态规则：
        - upcoming: 活动未开始（start_time > 当前时间）
        - ongoing: 活动进行中（start_time <= 当前时间 < start_time + 24小时）
        - ended: 活动已结束（当前时间 >= start_time + 24小时）

        返回：
        - str: 计算后的状态
        """
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        
        if self.start_time > now:
            return 'upcoming'
        
        end_time = self.start_time + timedelta(hours=24)
        if now < end_time:
            return 'ongoing'
        
        return 'ended'

    def to_dict(self, include_registrations=True, mask_registrations=True, show_contact=False, is_organizer=False):
        """
        将活动对象转换为可 JSON 序列化的字典。

        参数：
        - include_registrations: 是否包含报名与签到明细（列表页通常关闭）
        - mask_registrations: 是否对报名手机号脱敏（非组织者视角应开启）
        - show_contact: 是否显示主办方联系方式（已报名用户可见）
        - is_organizer: 是否是活动组织者（组织者可见完整联系方式）

        返回：
        - dict: 活动字段快照
        """
        calculated_status = self.calculate_status()
        
        res = {
            'id': self.id,
            'organizer_id': self.user_id,
            'name': self.name,
            'type': self.type,
            'start_time': self.start_time.isoformat(),
            'location': self.location,
            'description': self.description,
            'capacity': self.capacity,
            'status': calculated_status,
            'views_count': self.views_count,
            'created_at': self.created_at.isoformat(),
        }
        
        if show_contact or is_organizer:
            if self.show_phone and self.host_phone:
                res['host_phone'] = self.host_phone if is_organizer else mask_phone(self.host_phone)
            if self.show_wechat and self.host_wechat:
                res['host_wechat'] = self.host_wechat if is_organizer else self._mask_wechat(self.host_wechat)
        
        if include_registrations:
            res['registrations'] = [r.to_dict(mask=mask_registrations) for r in self.registrations]
            res['checkin_records'] = [c.to_dict() for c in self.checkin_records]
            
        return res
    
    def _mask_wechat(self, wechat):
        """微信号脱敏处理，如 wechat_id -> wch****id"""
        if not wechat or len(wechat) < 4:
            return wechat
        return f"{wechat[:2]}****{wechat[-2:]}"

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

    def to_dict(self, mask=False):
        """
        将报名对象转换为可 JSON 序列化的字典。

        参数：
        - mask: 是否对手机号脱敏

        返回：
        - dict: 报名字段快照，并包含 checked_in 字段用于前端展示。
        """
        return {
            'id': self.id,
            'activity_id': self.activity_id,
            'name': self.name,
            'phone': mask_phone(self.phone) if mask else self.phone,
            'created_at': self.created_at.isoformat(),
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
        """
        将签到记录转换为可 JSON 序列化的字典。
        """
        return {
            'id': self.id,
            'registration_id': self.registration_id,
            'activity_id': self.activity_id,
            'checkin_time': self.checkin_time.isoformat()
        }

class Report(db.Model):
    """
    举报模型
    存储用户对活动的举报信息。
    """
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    # 被举报的活动 ID
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    # 举报人 ID (Mock)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # 举报原因分类
    reason = db.Column(db.String(50), nullable=False)
    # 举报详情（可选）
    detail = db.Column(db.Text)
    # 处理状态：pending(待处理), processed(已处理), rejected(已驳回)
    status = db.Column(db.String(20), default='pending')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """
        将举报记录转换为可 JSON 序列化的字典。
        """
        return {
            'id': self.id,
            'activity_id': self.activity_id,
            'user_id': self.user_id,
            'reason': self.reason,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class IdempotencyKey(db.Model):
    """
    幂等键记录表（写接口防重）。

    业务背景：
    - 前端存在离线队列与弱网重试机制，同一写操作可能被多次提交；
    - 通过客户端生成的 `Idempotency-Key` 把“同一次业务写入”映射为唯一 key；
    - 服务端首次处理后持久化响应；后续同 key 且指纹一致的请求直接复放（replay）。

    关键字段说明：
    - key: 客户端生成的幂等键（唯一）。
    - request_hash: method/path/body 的指纹，用于检测“同 key 不同语义”的冲突。
    - response_status/response_body: 首次请求的响应快照，用于复放。
    """
    __tablename__ = 'idempotency_keys'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    method = db.Column(db.String(10), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    request_hash = db.Column(db.String(64), nullable=False)
    response_status = db.Column(db.Integer, nullable=False)
    response_body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Org(db.Model):
    """
    组织/主办方（租户）模型。

    设计目标：
    - 为未来“团队协作”“多成员共同管理活动”“商业化订阅按组织计费”等能力预埋；
    - 当前实现为“每个用户默认拥有一个主办方组织”，owner_user_id 唯一。
    """
    __tablename__ = 'orgs'

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    name = db.Column(db.String(128), nullable=False, default='默认主办方')
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    members = db.relationship('OrgMember', backref='org', lazy='dynamic', cascade='all, delete-orphan')


class OrgMember(db.Model):
    """
    组织成员关系表。

    约束：
    - (org_id, user_id) 唯一，避免重复加入；
    - role/status 用于后续权限控制与成员生命周期管理。
    """
    __tablename__ = 'org_members'

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('orgs.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    role = db.Column(db.String(20), default='owner')
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('org_id', 'user_id', name='uq_org_member'),
    )


class Plan(db.Model):
    """
    套餐定义（计费层的“商品”）。

    字段语义：
    - code: 业务唯一标识（用于前端/配置引用）。
    - period: 计费周期（预留：month/year 等）。
    - status: active/inactive（仅 active 对外展示）。
    - sort: 展示排序。
    """
    __tablename__ = 'plans'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    period = db.Column(db.String(20), default='month')
    status = db.Column(db.String(20), default='inactive')
    sort = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Entitlement(db.Model):
    """
    权益定义（能力开关/配额项）。

    设计方式：
    - key: 权益键（如 export.enabled / activity.max_count）。
    - type: bool/int/string（用于值解析）。
    - default_value: 无订阅或订阅无效时的默认值。
    """
    __tablename__ = 'entitlements'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    type = db.Column(db.String(20), default='bool')
    default_value = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PlanEntitlement(db.Model):
    """
    套餐-权益映射表：为某套餐配置具体权益值。

    约束：
    - (plan_id, entitlement_key) 唯一，避免同一套餐重复配置同一权益。
    """
    __tablename__ = 'plan_entitlements'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False, index=True)
    entitlement_key = db.Column(db.String(100), db.ForeignKey('entitlements.key'), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('plan_id', 'entitlement_key', name='uq_plan_entitlement'),
    )


class Subscription(db.Model):
    """
    订阅记录：某组织在某一时间段内订阅了哪个套餐。

    字段语义：
    - status: trialing/active/canceled 等（当前逻辑对 trialing/active 生效）。
    - start_at/end_at: 生效区间，用于过期判定。
    - provider/external_ref: 支付渠道对接预留（如 wechat/alipay/apple 等）。
    """
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('orgs.id'), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='trialing')
    start_at = db.Column(db.DateTime, nullable=True)
    end_at = db.Column(db.DateTime, nullable=True, index=True)
    provider = db.Column(db.String(20), default='manual')
    external_ref = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BillingEvent(db.Model):
    """
    计费事件流水（审计/对账预留）。

    用途：
    - 记录订阅开通、续费、手动授予等事件；
    - payload 保存事件上下文（JSON 字符串）。
    """
    __tablename__ = 'billing_events'

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('orgs.id'), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class SupportSession(db.Model):
    """
    客服会话记录（用户支持数据留痕）。

    用途：
    - 记录用户进入客服的来源（entry_point/scene）、平台、响应时长等指标；
    - 支撑后续 SLA、满意度与常见问题分类统计。
    """
    __tablename__ = 'support_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    org_id = db.Column(db.Integer, db.ForeignKey('orgs.id'), nullable=True, index=True)
    platform = db.Column(db.String(20), nullable=False)
    entry_point = db.Column(db.String(50), nullable=False, default='unknown')
    status = db.Column(db.String(20), nullable=False, default='opened')
    opened_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)
    first_response_ms = db.Column(db.Integer, nullable=True)
    satisfaction = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    external_session_id = db.Column(db.String(128), nullable=True)
    context_snapshot = db.Column(db.Text, nullable=True)


class EventLog(db.Model):
    """
    埋点事件明细表。

    设计要点：
    - 支持匿名上报：user_id/org_id 可为空；
    - request_id 关联后端链路，方便定位“某一次接口调用触发的埋点”；
    - properties 以 JSON 字符串存储，便于低成本扩展事件字段。
    """
    __tablename__ = 'event_logs'

    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(80), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    org_id = db.Column(db.Integer, db.ForeignKey('orgs.id'), nullable=True, index=True)
    platform = db.Column(db.String(20), nullable=False)
    app_version = db.Column(db.String(20), nullable=True)
    device_id = db.Column(db.String(64), nullable=True)
    request_id = db.Column(db.String(64), nullable=True, index=True)
    properties = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class MetricsDaily(db.Model):
    """
    日维度聚合指标表（预留）。

    约束：
    - (date, org_id, metric_key) 唯一，避免同日同指标重复写入；
    - org_id 可为空，用于全局指标（不区分组织）的场景。
    """
    __tablename__ = 'metrics_daily'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    org_id = db.Column(db.Integer, db.ForeignKey('orgs.id'), nullable=True, index=True)
    metric_key = db.Column(db.String(50), nullable=False)
    metric_value = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('date', 'org_id', 'metric_key', name='uq_metrics_daily'),
    )
