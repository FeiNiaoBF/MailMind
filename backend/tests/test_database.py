"""
数据库操作测试模块
"""
import pytest
from backend.app import db
from backend.app.db.models import User, Email, Task
from backend.app.utils.random import random_email


class TestUser:
    """
    测试用户类
    """

    def test_create_user(self, app):
        """
        测试创建用户
        """
        # 激活上下文
        with app.app_context():
            # 第一步：测试用户能否成功创建
            # 创建新用户
            em = random_email()
            user = User(email=em)
            db.session.add(user)
            db.session.commit()
            # 验证用户属性
            assert user.id is not None  # 检查是否生成ID
            assert user.email == em
            assert user.created_at is not None  # 检查自动生成的时间戳

    def test_get_user(self, app):
        """
        测试获取用户
        """
        with app.app_context():
            # 创建新用户
            em = random_email()
            user = User(email=em)
            db.session.add(user)
            db.session.commit()
            # 查询用户
            queried_user = db.session.get(User, user.id)
            assert queried_user is not None
            assert queried_user.email == em

    def test_update_user(self, app):
        """
        测试更新用户
        """
        with app.app_context():
            # 创建新用户
            em = random_email()
            user = User(email=em)
            db.session.add(user)
            db.session.commit()
            # 更新用户
            new_em = random_email()
            user.email = new_em
            db.session.commit()
            # 查询用户
            queried_user = db.session.get(User, user.id)
            assert queried_user is not None
            assert queried_user.email == new_em

    def test_delete_user(self, app):
        """
        测试删除用户
        """
        with app.app_context():
            # 创建新用户
            em = random_email()
            user = User(email=em)
            db.session.add(user)
            db.session.commit()
            # 删除用户
            db.session.delete(user)
            db.session.commit()
            # 查询用户
            queried_user = db.session.get(User, user.id)
            assert queried_user is None
