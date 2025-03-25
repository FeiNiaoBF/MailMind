"""
测试配置文件
"""
import os
import pytest
import shutil
from datetime import datetime, UTC
from flask import Flask, current_app
from flask_jwt_extended import JWTManager, create_access_token
from backend.app.config.config import TestingConfig
from backend.app.db.database import db, init_db
from backend.app.db.models import User, Email, Analysis, Task
from backend.app.service.email.auth import EmailAuthService
from backend.app.service.email.sync import EmailSyncService
from backend.app.service.email.analysis import EmailAnalysisService
from backend.app.api.auth import auth_bp
from backend.app import create_app
from unittest.mock import patch, Mock

# 设置测试环境
os.environ['FLASK_ENV'] = 'testing'


@pytest.fixture(scope='session')
def app():
    """创建测试应用实例"""
    app = create_app('testing')

    # 创建应用上下文
    with app.app_context():
        db.create_all()

    yield app

    # 清理数据库
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """创建数据库会话"""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        session = db._make_scoped_session(
            options={"bind": connection, "binds": {}}
        )
        db.session = session

        yield session

        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture(scope='function')
def auth_headers(test_user):
    """创建认证头"""
    access_token = create_access_token(identity=test_user.id)
    return {'Authorization': f'Bearer {access_token}'}


# 邮件模块
@pytest.fixture(scope='function')
def gmail_auth_service():
    """创建Gmail认证服务实例"""
    return EmailAuthService()


@pytest.fixture(scope='function')
def email_sync_service():
    """创建邮件同步服务实例"""
    return EmailSyncService()


@pytest.fixture(scope='function')
def email_analysis_service():
    """创建邮件AI分析服务实例"""
    return EmailAnalysisService()


@pytest.fixture(scope='function')
def test_user(db_session):
    """创建测试用户"""
    user = User(
        email=current_app.config['TEST_USER_EMAIL'],
        oauth_uid=current_app.config['TEST_USER_OAUTH_UID'],
        oauth_token={
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_at': datetime.now(UTC).isoformat()
        },
        oauth_provider=current_app.config['TEST_USER_OAUTH_PROVIDER'],
        is_active=True,
        oauth_token_expires_at=datetime.now(UTC)
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope='function')
def test_email(db_session, test_user):
    """创建测试邮件"""
    email = Email(
        user_id=test_user.id,
        uid=12345,
        message_id='test_message_id',
        from_header='sender@example.com',
        to_header='recipient@example.com',
        subject='Test Subject',
        body='Test Body',
        html_body='<p>Test Body</p>',
        received_at=datetime.now(UTC),
        raw_headers={'header1': 'value1'},
        attachments=[{'name': 'test.txt', 'size': 100}],
        labels=['INBOX'],
        size=1000
    )
    db_session.add(email)
    db_session.commit()
    return email


@pytest.fixture(scope='function')
def test_analysis(db_session, test_email):
    """创建测试分析结果"""
    analysis = Analysis(
        email_uid=test_email.uid,
        analysis_type='summary',
        result={'summary': 'Test summary'},
        analyzed_at=datetime.now(UTC),
        model_used='gpt-3.5-turbo'
    )
    db_session.add(analysis)
    db_session.commit()
    return analysis


@pytest.fixture(scope='function')
def test_task(db_session, test_user, test_email):
    """创建测试任务"""
    task = Task(
        user_id=test_user.id,
        mail_uid=str(test_email.uid),
        task_type='analyze',
        task_data={'type': 'summary'},
        status='pending',
        model_used='gpt-3.5-turbo'
    )
    db_session.add(task)
    db_session.commit()
    return task


@pytest.fixture(scope='function')
def mock_gmail_api():
    """模拟Gmail API"""
    with patch('googleapiclient.discovery.build') as mock_build:
        mock_service = Mock()
        mock_build.return_value = mock_service
        yield mock_service


@pytest.fixture(scope='function')
def mock_ai_service():
    """模拟AI服务"""
    with patch('backend.app.service.email.analysis.EmailAnalysisService.analyze_email') as mock_analyze:
        mock_analyze.return_value = {
            'summary': 'Test summary',
            'keywords': ['test', 'email'],
            'sentiment': 'positive'
        }
        yield mock_analyze
