import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from src.api.main import app
from src.db.database import SessionLocal, Base, engine
from src.db import models

# Use test database
test_db_url = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create test database."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield SessionLocal()
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root health check."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data
    
    def test_health_endpoint(self, client):
        """Test detailed health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAdEndpoints:
    """Tests for ad-related endpoints."""
    
    def test_get_ads_empty(self, client):
        """Test getting ads when none exist."""
        response = client.get("/ads/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_ads_not_found(self, client):
        """Test getting non-existent ad."""
        response = client.get("/ads/999")
        assert response.status_code == 404


class TestSearchEndpoints:
    """Tests for search endpoints."""
    
    def test_semantic_search_empty(self, client):
        """Test search on empty database."""
        response = client.post("/search/", json={
            "query_text": "luxury watches",
            "limit": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "luxury watches"
        assert data["total"] == 0
    
    def test_semantic_search_limit_validation(self, client):
        """Test search with invalid limit."""
        response = client.post("/search/", json={
            "query_text": "test",
            "limit": 101  # Over max
        })
        assert response.status_code == 422  # Validation error
