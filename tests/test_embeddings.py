import pytest
from src.embeddings.embedder import EmbeddingService, embed_text, embed_texts, EMBEDDING_DIM


class TestEmbeddingService:
    """Tests for the embedding service."""
    
    @pytest.fixture
    def embedder(self):
        """Create embedder instance."""
        return EmbeddingService()
    
    def test_embed_text(self, embedder):
        """Test embedding a single text."""
        text = "Best luxury watches for professionals"
        embedding = embedder.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIM
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_texts(self, embedder):
        """Test batch embedding."""
        texts = [
            "Buy luxury watches",
            "Discount on designer shoes",
            "Limited time offer"
        ]
        embeddings = embedder.embed_texts(texts)
        
        assert len(embeddings) == len(texts)
        assert all(len(e) == EMBEDDING_DIM for e in embeddings)
    
    def test_embed_ad_creative(self, embedder):
        """Test embedding ad creative components."""
        embedding = embedder.embed_ad_creative(
            headline="Exclusive Watch Collection",
            caption="Limited edition luxury watches",
            cta="Shop Now"
        )
        
        assert len(embedding) == EMBEDDING_DIM
    
    def test_embed_empty_text(self, embedder):
        """Test handling of empty text."""
        embedding = embedder.embed_text("")
        assert len(embedding) == EMBEDDING_DIM
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Single text
        embedding = embed_text("Test query")
        assert len(embedding) == EMBEDDING_DIM
        
        # Multiple texts
        embeddings = embed_texts(["Text 1", "Text 2"])
        assert len(embeddings) == 2
        assert all(len(e) == EMBEDDING_DIM for e in embeddings)
    
    def test_embedding_consistency(self, embedder):
        """Test that same text produces same embedding."""
        text = "Consistent embedding test"
        embedding1 = embedder.embed_text(text)
        embedding2 = embedder.embed_text(text)
        
        # Should be very close (allowing for float precision)
        assert embedding1 == embedding2
