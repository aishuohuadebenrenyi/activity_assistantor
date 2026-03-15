"""
法务页面（静态 HTML）可用性测试。

目的：
- 确保隐私政策与用户协议页面在后端路由下可正常访问；
- 用于满足平台合规检查与回归验证。
"""

import pytest
from backend.app import create_app


@pytest.fixture
def app():
    class TestConfig:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SECRET_KEY = "test_secret"
        WECHAT_APPID = "mock_appid"
        WECHAT_SECRET = "mock_secret"
        SQLALCHEMY_TRACK_MODIFICATIONS = False

    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


def test_legal_privacy_page(client):
    response = client.get("/legal/privacy")
    assert response.status_code == 200
    assert "text/html" in response.content_type
    assert "隐私政策" in response.get_data(as_text=True)


def test_legal_terms_page(client):
    response = client.get("/legal/terms")
    assert response.status_code == 200
    assert "text/html" in response.content_type
    assert "用户协议" in response.get_data(as_text=True)
