"""
测试配置文件
"""
import pytest
from app import create_app
from app.db.database import db
from app.models import User, Email


@pytest.fixture(scope='module')
def app():
    """应用工厂"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()  # 确保在模块级别创建表
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope='function')
def db_session(app):
    """数据库会话配置"""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()  # 使用普通事务代替嵌套事务

        # 绑定会话到连接
        session = db.session
        session.configure(bind=connection)

        yield session
        # 清理操作
        session.rollback()
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def mock_test_user(db_session):
    """创建测试用户"""
    user = User(
        email='test@example.com',
        provider_id='test_provider_id',
        auth_provider='google'
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_headers(mock_test_user, app):
    """创建认证头"""
    from flask_jwt_extended import create_access_token

    with app.app_context():
        access_token = create_access_token(identity=mock_test_user.id)

    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
