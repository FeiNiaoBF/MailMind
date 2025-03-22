"""
Basic tests for the Flask application.
"""
import pytest
from app import create_app
from app.config.config import TestingConfig


@pytest.fixture
def app():
    """Create application for the tests."""
    app = create_app(config_class=TestingConfig)
    app.config.update({
        "TESTING": True,
    })
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_index(client):
    """测试首页端点"""
    response = client.get("/api/")
    assert response.status_code == 200
    assert "message" in response.json
