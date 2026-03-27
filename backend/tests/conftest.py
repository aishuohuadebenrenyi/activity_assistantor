"""
测试配置和公共Fixtures

提供测试所需的通用配置和工具函数。
"""

import pytest
import jwt
import datetime
from backend.app import create_app
from backend.models import db, User, Activity, Registration, CheckinRecord


class TestConfig:
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test_secret_key_for_testing_only"
    WECHAT_APPID = "test_appid"
    WECHAT_SECRET = "test_secret"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = "WARNING"


@pytest.fixture(scope="session")
def app():
    """创建测试应用实例"""
    test_app = create_app(TestConfig)
    
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建CLI测试运行器"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """创建测试用户"""
    with app.app_context():
        user = User(
            phone="13800138000",
            username="测试用户",
            avatar_url="https://example.com/avatar.png"
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_organizer(app):
    """创建主办方用户"""
    with app.app_context():
        user = User(
            phone="13900139000",
            username="主办方用户",
            avatar_url="https://example.com/organizer.png"
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def auth_header(app, test_user):
    """生成认证头"""
    with app.app_context():
        user = db.session.get(User, test_user.id)
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def organizer_auth_header(app, test_organizer):
    """生成主办方认证头"""
    with app.app_context():
        user = db.session.get(User, test_organizer.id)
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def test_activity(app, test_organizer):
    """创建测试活动"""
    with app.app_context():
        user = db.session.get(User, test_organizer.id)
        activity = Activity(
            user_id=user.id,
            name="测试活动",
            type="business",
            start_time=datetime.datetime.utcnow() + datetime.timedelta(days=7),
            end_time=datetime.datetime.utcnow() + datetime.timedelta(days=7, hours=2),
            location="北京市朝阳区测试大厦",
            description="这是一个测试活动",
            capacity=100,
            host_phone="13900139000",
            host_wechat="test_wechat",
            show_phone=True,
            show_wechat=True
        )
        db.session.add(activity)
        db.session.commit()
        return activity


@pytest.fixture
def test_registration(app, test_activity, test_user):
    """创建测试报名记录"""
    with app.app_context():
        activity = db.session.get(Activity, test_activity.id)
        user = db.session.get(User, test_user.id)
        registration = Registration(
            activity_id=activity.id,
            user_id=user.id,
            name="报名用户",
            phone="13800138000"
        )
        db.session.add(registration)
        db.session.commit()
        return registration


@pytest.fixture
def test_checkin_record(app, test_registration):
    """创建测试签到记录"""
    with app.app_context():
        registration = db.session.get(Registration, test_registration.id)
        checkin = CheckinRecord(
            registration_id=registration.id,
            activity_id=registration.activity_id,
            checkin_time=datetime.datetime.utcnow()
        )
        db.session.add(checkin)
        db.session.commit()
        return checkin


class TestUtils:
    """测试工具类"""
    
    @staticmethod
    def create_user(phone, username="测试用户"):
        """创建用户"""
        user = User(phone=phone, username=username)
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def create_activity(user_id, **kwargs):
        """创建活动"""
        defaults = {
            'name': "测试活动",
            'type': "business",
            'start_time': datetime.datetime.utcnow() + datetime.timedelta(days=7),
            'location': "测试地点",
            'capacity': 100
        }
        defaults.update(kwargs)
        activity = Activity(user_id=user_id, **defaults)
        db.session.add(activity)
        db.session.commit()
        return activity
    
    @staticmethod
    def create_registration(activity_id, user_id, name, phone):
        """创建报名记录"""
        registration = Registration(
            activity_id=activity_id,
            user_id=user_id,
            name=name,
            phone=phone
        )
        db.session.add(registration)
        db.session.commit()
        return registration
