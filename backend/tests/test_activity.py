"""
活动相关接口的后端单元测试（pytest）。

覆盖范围：
- 创建活动（含鉴权）；
- 获取活动列表；
- 未登录删除活动的鉴权校验；
- 举报接口的基本可用性。
"""

import pytest
import json
import jwt
import datetime
from backend.app import create_app
from backend.models import db, User, Activity

@pytest.fixture
def app():
    class TestConfig:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SECRET_KEY = "test_secret"
        WECHAT_APPID = "mock_appid"
        WECHAT_SECRET = "mock_secret"
        SQLALCHEMY_TRACK_MODIFICATIONS = False

    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        # Create a test user
        user = User(phone="13800000000", username="Test User")
        db.session.add(user)
        db.session.commit()
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_header(app):
    with app.app_context():
        user = User.query.first()
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return {'Authorization': f'Bearer {token}'}

def test_create_activity(client, auth_header):
    payload = {
        "name": "Test Activity",
        "type": "business",
        "date": "2026-10-01",
        "time": "10:00",
        "location": "Test Location",
        "description": "Test Description",
        "capacity": 100
    }
    response = client.post('/api/activities/', json=payload, headers=auth_header)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == "Test Activity"
    assert data['organizer_id'] == 1

def test_get_activities(client):
    response = client.get('/api/activities/')
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_delete_activity_unauthorized(client):
    response = client.delete('/api/activities/1')
    assert response.status_code == 401 # No token

def test_report_activity(client, auth_header, app):
    with app.app_context():
        # Create an activity first
        user = User.query.first()
        act = Activity(user_id=user.id, name="Report Me", start_time=datetime.datetime.utcnow())
        db.session.add(act)
        db.session.commit()
        act_id = act.id

    payload = {"reason": "垃圾广告"}
    response = client.post(f'/api/activities/{act_id}/report', json=payload, headers=auth_header)
    assert response.status_code == 200
    assert "举报已收到" in response.get_json()['message']
