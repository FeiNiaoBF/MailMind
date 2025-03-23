"""
测试配置文件
"""
import os
import pytest
from backend.app import create_app, db
from backend.app.db.database import init_db
from backend.app.utils.random import random_email

# 设置测试环境
os.environ['FLASK_ENV'] = 'testing'

BASE_TEST_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='session')
def app():
    """创建测试应用实例"""
    app = create_app('testing')

    # 确保数据库只被初始化一次
    with app.app_context():
        if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
            init_db(app)
        db.create_all()

    yield app

    # 清理数据库
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建测试运行器"""
    return app.test_cli_runner()


# 邮件模块
@pytest.fixture
def email_auth_service():
    """创建邮箱认证服务实例"""
    return EmailAuthService()


@pytest.fixture
def test_email():
    """测试邮箱"""
    em = random_email()
    return em
