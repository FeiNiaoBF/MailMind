"""
Basic tests for the Flask application.
"""
import pytest
from flask import current_app
from sqlalchemy import text
from backend.app.utils.logger import debug_print

from ..app import create_app
from ..app.config.config import config


@pytest.fixture
def app():
    """Create application for the tests."""
    app = create_app('testing')
    app.config.update({
        "TESTING": True,
    })

    # 创建数据库表
    with app.app_context():
        from ..app.db.database import db
        db.create_all()

    yield app

    # 清理数据库
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get("/api/v1/health")
    debug_print('response:', response.json)
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'
    assert response.json['message'] == 'Service is running'


def test_index(client):
    """测试首页端点"""
    response = client.get("/api/v1/")
    assert response.status_code == 200
    assert "message" in response.json


def test_something(app):
    with app.app_context():
        debug_print("测试信息")


def test_app_config(app):
    """测试应用配置"""
    assert app.config['TESTING'] is True
    assert app.config['DEBUG'] is True
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    assert app.config['EMAIL_PROVIDER'] == 'mailtrap'


def test_debug_print(app):
    """测试调试打印功能"""
    with app.app_context():
        debug_print("测试调试信息")
        debug_print("带参数的调试信息", param1="value1", param2="value2")


def test_database(app, db_session):
    """测试数据库连接"""
    with app.app_context():
        # 执行一个简单的查询来测试数据库连接
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_test_user(app, test_user):
    """测试测试用户"""
    assert test_user.email == current_app.config['TEST_USER_EMAIL']
    assert test_user.oauth_provider == current_app.config['TEST_USER_OAUTH_PROVIDER']
    assert test_user.is_active is True
