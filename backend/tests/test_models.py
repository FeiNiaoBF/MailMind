"""
测试模型
"""
import pytest
from datetime import datetime
from backend.app.models import User, Email, Analysis


def test_user_creation(db_session):
    """测试用户创建"""
    # 创建用户
    user = User(
        email='test@example.com',
        oauth_uid='123456',
        oauth_provider='gmail'
    )
    db_session.add(user)
    db_session.commit()

    # 验证用户属性
    assert user.email == 'test@example.com'
    assert user.oauth_uid == '123456'
    assert user.oauth_provider == 'gmail'
    assert user.is_active is True
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.last_login, datetime)


def test_user_update_oauth_token(db_session):
    """测试更新OAuth令牌"""
    # 创建用户
    user = User(
        email='test@example.com',
        oauth_uid='123456',
        oauth_provider='gmail'
    )
    db_session.add(user)
    db_session.commit()

    # 记录原始登录时间
    original_login = user.last_login

    # 更新令牌
    new_token = {
        'access_token': 'new_access_token',
        'refresh_token': 'new_refresh_token',
        'expires_at': datetime.utcnow().isoformat()
    }
    user.update_oauth_token(new_token)
    db_session.commit()

    # 验证更新
    assert user.oauth_token == new_token
    assert user.last_login > original_login


def test_user_to_dict(db_session):
    """测试用户字典转换"""
    # 创建用户
    user = User(
        email='test@example.com',
        oauth_uid='123456',
        oauth_provider='gmail'
    )
    db_session.add(user)
    db_session.commit()

    # 转换为字典
    user_dict = user.to_dict()

    # 验证字典内容
    assert user_dict['email'] == 'test@example.com'
    assert user_dict['is_active'] is True
    assert user_dict['oauth_provider'] == 'gmail'
    assert isinstance(user_dict['created_at'], str)
    assert isinstance(user_dict['last_login'], str)


def test_user_relationships(db_session):
    """测试用户关系"""
    # 创建用户
    user = User(
        email='test@example.com',
        oauth_uid='123456',
        oauth_provider='gmail'
    )
    db_session.add(user)
    db_session.commit()

    # 创建邮件
    email = Email(
        user_id=user.id,
        uid='12345',
        message_id='test_message_id',
        from_header='sender@example.com',
        to_header='recipient@example.com',
        subject='Test Subject',
        body='Test Body',
        received_at=datetime.utcnow()
    )
    db_session.add(email)
    db_session.commit()

    # 创建分析
    analysis = Analysis(
        user_id=user.id,
        email_uid=email.uid,
        analysis_type='summary',
        result={'summary': 'Test summary'},
        analyzed_at=datetime.utcnow()
    )
    db_session.add(analysis)
    db_session.commit()

    # 验证关系
    assert len(user.emails) == 1
    assert user.emails[0].uid == '12345'
    assert len(user.analyses) == 1
    assert user.analyses[0].analysis_type == 'summary'


def test_user_unique_constraints(db_session):
    """测试用户唯一性约束"""
    # 创建第一个用户
    user1 = User(
        email='test@example.com',
        oauth_uid='123456',
        oauth_provider='gmail'
    )
    db_session.add(user1)
    db_session.commit()

    # 尝试创建具有相同邮箱的用户
    user2 = User(
        email='test@example.com',  # 重复的邮箱
        oauth_uid='789012',
        oauth_provider='gmail'
    )
    db_session.add(user2)
    with pytest.raises(Exception):  # 应该抛出异常
        db_session.commit()

    # 尝试创建具有相同oauth_uid的用户
    user3 = User(
        email='another@example.com',
        oauth_uid='123456',  # 重复的oauth_uid
        oauth_provider='gmail'
    )
    db_session.add(user3)
    with pytest.raises(Exception):  # 应该抛出异常
        db_session.commit()
