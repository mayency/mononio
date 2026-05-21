import pytest
from datetime import datetime
from src.api import schemas


class TestAdSchemas:
    """Tests for ad-related schemas."""
    
    def test_ad_create_schema(self):
        """Test ad creation schema validation."""
        ad_data = {
            "platform": "facebook",
            "advertiser_id": "adv123",
            "brand_name": "BrandX",
            "is_active": True,
            "start_date": datetime.now()
        }
        ad = schemas.AdCreate(**ad_data)
        assert ad.brand_name == "BrandX"
        assert ad.platform == "facebook"
    
    def test_ad_response_schema(self):
        """Test ad response schema with from_attributes."""
        ad_data = {
            "id": 1,
            "platform": "facebook",
            "advertiser_id": "adv123",
            "brand_name": "BrandX",
            "is_active": True,
            "start_date": datetime.now(),
            "end_date": None,
            "active_days": 30,
            "longevity_score": 0.85,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        ad = schemas.AdResponse(**ad_data)
        assert ad.id == 1
        assert ad.longevity_score == 0.85


class TestSearchSchemas:
    """Tests for search-related schemas."""
    
    def test_search_query_schema(self):
        """Test search query validation."""
        query = schemas.SearchQuery(
            query_text="luxury watches",
            limit=10
        )
        assert query.query_text == "luxury watches"
        assert query.limit == 10
    
    def test_search_query_limit_validation(self):
        """Test search query limit bounds."""
        # Should accept valid limit
        query = schemas.SearchQuery(query_text="test", limit=50)
        assert query.limit == 50
        
        # Should fail on limit > 100
        with pytest.raises(ValueError):
            schemas.SearchQuery(query_text="test", limit=101)
    
    def test_search_response_schema(self):
        """Test search response schema."""
        response = schemas.SearchResponse(
            query="luxury watches",
            results=[],
            total=0
        )
        assert response.query == "luxury watches"
        assert response.total == 0
