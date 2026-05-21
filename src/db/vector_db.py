import os
import logging
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

QDANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDANT_COLLECTION = "ad_creatives"
VECTOR_SIZE = 384  # MiniLM-L6-v2 embedding size

try:
    client = QdrantClient(url=QDRANT_URL)
except Exception as e:
    logger.error(f"Failed to connect to Qdrant at {QDRANT_URL}: {e}")
    client = None


def init_qdrant():
    """
    Initializes the Qdrant collection if it doesn't exist.
    Creates collection with cosine distance metric and 384-dim vectors.
    """
    if not client:
        logger.warning("Qdrant client not initialized")
        return
    
    try:
        collections = client.get_collections().collections
        exists = any(c.name == QDRANT_COLLECTION for c in collections)
        
        if not exists:
            client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {QDRANT_COLLECTION}")
        else:
            logger.info(f"Qdrant collection already exists: {QDRANT_COLLECTION}")
    except Exception as e:
        logger.error(f"Error initializing Qdrant: {e}")
        raise


def upsert_vector(point_id: int, vector: List[float], payload: Dict[str, Any]):
    """
    Store embeddings with metadata in Qdrant.
    
    Args:
        point_id: Unique ID for the creative
        vector: 384-dimensional embedding vector
        payload: Metadata (brand, platform, url, etc.)
    """
    if not client:
        logger.warning("Qdrant client not initialized, skipping upsert")
        return
    
    if len(vector) != VECTOR_SIZE:
        logger.error(f"Vector size mismatch: expected {VECTOR_SIZE}, got {len(vector)}")
        raise ValueError(f"Vector must be {VECTOR_SIZE}-dimensional")
    
    try:
        point = PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )
        client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[point]
        )
        logger.info(f"Upserted vector {point_id} to Qdrant")
    except Exception as e:
        logger.error(f"Vector upsert error: {e}")
        raise


def search_vectors(query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for similar vectors in Qdrant.
    
    Args:
        query_vector: 384-dimensional query embedding
        limit: Number of results to return
    
    Returns:
        List of matching results with scores and metadata
    """
    if not client:
        logger.warning("Qdrant client not initialized, returning empty results")
        return []
    
    if len(query_vector) != VECTOR_SIZE:
        logger.error(f"Query vector size mismatch: expected {VECTOR_SIZE}, got {len(query_vector)}")
        raise ValueError(f"Query vector must be {VECTOR_SIZE}-dimensional")
    
    try:
        search_result = client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_vector,
            limit=limit
        )
        logger.info(f"Qdrant search returned {len(search_result)} results")
        return search_result
    except Exception as e:
        logger.error(f"Qdrant search error: {e}")
        return []


def delete_vector(point_id: int):
    """
    Delete a vector from Qdrant by ID.
    
    Args:
        point_id: ID of the point to delete
    """
    if not client:
        logger.warning("Qdrant client not initialized, skipping delete")
        return
    
    try:
        client.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=point_id
        )
        logger.info(f"Deleted vector {point_id} from Qdrant")
    except Exception as e:
        logger.error(f"Vector delete error: {e}")
        raise


def get_collection_stats() -> Dict[str, Any]:
    """
    Get stats about the Qdrant collection.
    """
    if not client:
        logger.warning("Qdrant client not initialized")
        return {}
    
    try:
        stats = client.get_collection(QDRANT_COLLECTION)
        return {
            "name": QDRANT_COLLECTION,
            "points_count": stats.points_count,
            "vectors_count": stats.vectors_count,
        }
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {}
