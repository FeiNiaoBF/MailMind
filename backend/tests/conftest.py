"""
测试配置文件
"""
import pytest
from app import create_app


@pytest.fixture
def app():
    """创建测试应用实例"""
    app = create_app('testing')
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()
