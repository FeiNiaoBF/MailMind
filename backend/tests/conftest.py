"""
测试配置文件
"""
import os
import pytest
from backend.app import create_app, db
from backend.app.config.config import config
from backend.app.db.database import init_db
from backend.app.utils.logger import debug_print

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
