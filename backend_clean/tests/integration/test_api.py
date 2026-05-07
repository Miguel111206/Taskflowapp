import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client without database override."""
    from main import app
    return TestClient(app)


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root(self, client):
        """Test root returns message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestHealthEndpoint:
    """Tests for health endpoint."""
    
    def test_health(self, client):
        """Test health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"