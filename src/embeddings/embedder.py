import logging
from typing import List, Union
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Use the same model as Qdrant expects (384-dimensional)
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


class EmbeddingService:
    """
    Service for generating semantic embeddings for ad copy, headlines, and metadata.
    Uses SentenceTransformers for fast, efficient embeddings.
    """
    
    def __init__(self, model_name: str = MODEL_NAME):
        """
        Initialize the embedding model.
        
        Args:
            model_name: HuggingFace model identifier
        """
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {model_name}: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Input text to embed
        
        Returns:
            384-dimensional embedding vector
        """
        if not text or not isinstance(text, str):
            logger.warning(f"Invalid text input: {text}")
            return [0.0] * EMBEDDING_DIM
        
        try:
            embedding = self.model.encode(text.strip(), convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).
        More efficient than calling embed_text repeatedly.
        
        Args:
            texts: List of text strings
        
        Returns:
            List of embedding vectors
        """
        if not texts or not all(isinstance(t, str) for t in texts):
            logger.warning(f"Invalid texts input")
            return [[0.0] * EMBEDDING_DIM for _ in texts]
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            raise
    
    def embed_ad_creative(self, headline: str = "", caption: str = "", cta: str = "") -> List[float]:
        """
        Generate combined embedding for an ad creative by concatenating text fields.
        
        Args:
            headline: Ad headline
            caption: Ad caption/body
            cta: Call-to-action text
        
        Returns:
            Combined embedding vector
        """
        # Combine all text fields with separators
        combined_text = " ".join(filter(None, [headline, caption, cta]))
        
        if not combined_text:
            logger.warning("No text provided for ad creative embedding")
            return [0.0] * EMBEDDING_DIM
        
        return self.embed_text(combined_text)


# Singleton instance
_embedder = None


def get_embedder() -> EmbeddingService:
    """
    Get or create the embedding service singleton.
    
    Returns:
        EmbeddingService instance
    """
    global _embedder
    if _embedder is None:
        _embedder = EmbeddingService()
    return _embedder


def embed_text(text: str) -> List[float]:
    """
    Convenience function to embed text using the default service.
    
    Args:
        text: Text to embed
    
    Returns:
        Embedding vector
    """
    return get_embedder().embed_text(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Convenience function to embed multiple texts.
    
    Args:
        texts: List of texts
    
    Returns:
        List of embedding vectors
    """
    return get_embedder().embed_texts(texts)
