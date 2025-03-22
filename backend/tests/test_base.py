"""
Basic tests for the Flask application.
"""
import pytest
from app import create_app


@pytest.fixture
def app():
    """Create application for the tests."""
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_health_check(client):
    """Test 基本API健康检查."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_index(client):
    """Test the index endpoint."""
    response = client.get("/api/")
    assert response.status_code == 200
    assert "message" in response.json
