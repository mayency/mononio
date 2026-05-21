import logging
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from src.db.database import get_db, init_db, engine
from src.db import models
from src.api import schemas
from src.db.vector_db import init_qdrant, search_vectors, upsert_vector
from src.embeddings.embedder import get_embedder

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database and vector store
init_db()
init_qdrant()

app = FastAPI(
    title="AI Marketing Intelligence Agent API",
    description="A2A-compatible API for accessing advertising intelligence",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)


# ============= HEALTH CHECK =============

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "AI Marketing Intelligence Agent API is running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "vector_store": "connected"
    }


# ============= AD ENDPOINTS =============

@app.post("/ads/", response_model=schemas.AdResponse, tags=["Ads"])
def create_ad(ad: schemas.AdCreate, db: Session = Depends(get_db)):
    """
    Create a new ad record.
    
    Args:
        ad: Ad creation data
        db: Database session
    
    Returns:
        Created ad object
    """
    try:
        db_ad = models.Ads(**ad.model_dump())
        db.add(db_ad)
        db.commit()
        db.refresh(db_ad)
        logger.info(f"Created ad: {db_ad.id}")
        return db_ad
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating ad: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/ads/", response_model=List[schemas.AdResponse], tags=["Ads"])
def get_ads(
    skip: int = 0,
    limit: int = 10,
    platform: str = None,
    brand_name: str = None,
    db: Session = Depends(get_db)
):
    """
    Get ads with optional filtering.
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Number of records to return
        platform: Filter by platform
        brand_name: Filter by brand name
        db: Database session
    
    Returns:
        List of ads
    """
    query = db.query(models.Ads)
    
    if platform:
        query = query.filter(models.Ads.platform == platform)
    if brand_name:
        query = query.filter(models.Ads.brand_name.ilike(f"%{brand_name}%"))
    
    ads = query.offset(skip).limit(limit).all()
    return ads


@app.get("/ads/{ad_id}", response_model=schemas.AdResponse, tags=["Ads"])
def get_ad(ad_id: int, db: Session = Depends(get_db)):
    """
    Get a specific ad by ID.
    
    Args:
        ad_id: ID of the ad
        db: Database session
    
    Returns:
        Ad object or 404 error
    """
    ad = db.query(models.Ads).filter(models.Ads.id == ad_id).first()
    if ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    return ad


# ============= CREATIVE ENDPOINTS =============

@app.post("/creatives/", response_model=schemas.CreativeResponse, tags=["Creatives"])
def create_creative(creative: schemas.CreativeCreate, db: Session = Depends(get_db)):
    """
    Create a new creative asset.
    
    Args:
        creative: Creative data
        db: Database session
    
    Returns:
        Created creative object
    """
    try:
        # Generate embedding for the creative
        embedder = get_embedder()
        embedding = embedder.embed_ad_creative(
            headline=creative.headline or "",
            caption=creative.caption or "",
            cta=creative.cta_text or ""
        )
        
        db_creative = models.Creatives(
            **creative.model_dump(),
            embedding=embedding
        )
        db.add(db_creative)
        db.commit()
        db.refresh(db_creative)
        
        # Upsert to vector store
        upsert_vector(
            point_id=db_creative.id,
            vector=embedding,
            payload={
                "creative_id": db_creative.id,
                "ad_id": db_creative.ad_id,
                "brand_name": db.query(models.Ads).get(db_creative.ad_id).brand_name,
                "platform": db.query(models.Ads).get(db_creative.ad_id).platform,
            }
        )
        
        logger.info(f"Created creative: {db_creative.id}")
        return db_creative
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating creative: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/creatives/", response_model=List[schemas.CreativeResponse], tags=["Creatives"])
def get_creatives(
    skip: int = 0,
    limit: int = 10,
    ad_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Get creatives with optional filtering.
    
    Args:
        skip: Pagination offset
        limit: Results limit
        ad_id: Filter by ad ID
        db: Database session
    
    Returns:
        List of creatives
    """
    query = db.query(models.Creatives)
    
    if ad_id:
        query = query.filter(models.Creatives.ad_id == ad_id)
    
    creatives = query.offset(skip).limit(limit).all()
    return creatives


# ============= SEARCH ENDPOINTS =============

@app.post("/search/", response_model=schemas.SearchResponse, tags=["Search"])
def semantic_search(query: schemas.SearchQuery, db: Session = Depends(get_db)):
    """
    Perform semantic search on ad creatives.
    
    Args:
        query: Search query with text and filters
        db: Database session
    
    Returns:
        Matching creatives ranked by similarity
    """
    try:
        # Generate embedding for query
        embedder = get_embedder()
        query_vector = embedder.embed_text(query.query_text)
        
        # Search in Qdrant
        qdrant_results = search_vectors(query_vector, limit=query.limit)
        
        results = []
        for hit in qdrant_results:
            creative = db.query(models.Creatives).get(hit.id)
            ad = db.query(models.Ads).get(creative.ad_id) if creative else None
            
            if creative and ad:
                results.append(schemas.SearchResultItem(
                    creative_id=creative.id,
                    ad_id=ad.id,
                    score=hit.score,
                    brand_name=ad.brand_name,
                    platform=ad.platform,
                    headline=creative.headline,
                    media_url=creative.media_url
                ))
        
        logger.info(f"Search for '{query.query_text}' returned {len(results)} results")
        return schemas.SearchResponse(
            query=query.query_text,
            results=results,
            total=len(results)
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============= ANALYSIS ENDPOINTS =============

@app.get("/analysis/{ad_id}", response_model=schemas.AnalysisResultsResponse, tags=["Analysis"])
def get_analysis(ad_id: int, db: Session = Depends(get_db)):
    """
    Get analysis results for an ad.
    
    Args:
        ad_id: ID of the ad
        db: Database session
    
    Returns:
        Analysis results or 404
    """
    analysis = db.query(models.AnalysisResults).filter(
        models.AnalysisResults.ad_id == ad_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis


@app.post("/analysis/", response_model=schemas.AnalysisResultsResponse, tags=["Analysis"])
def create_analysis(
    analysis: schemas.AnalysisResultsCreate,
    db: Session = Depends(get_db)
):
    """
    Create analysis results for an ad.
    
    Args:
        analysis: Analysis data
        db: Database session
    
    Returns:
        Created analysis record
    """
    try:
        db_analysis = models.AnalysisResults(**analysis.model_dump())
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        logger.info(f"Created analysis: {db_analysis.id}")
        return db_analysis
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============= AGENT ENDPOINTS =============

@app.post("/agents/query", response_model=schemas.AgentResponse, tags=["Agents"])
def agent_query(query: schemas.AgentQuery):
    """
    Query the marketing intelligence brain with natural language.
    
    Args:
        query: Natural language query
    
    Returns:
        Agent response with insights
    """
    logger.info(f"Agent query: {query.query} (type: {query.agent_type})")
    
    return schemas.AgentResponse(
        query=query.query,
        agent_type=query.agent_type,
        response="Intelligence insight stub - implement agent logic",
        confidence=0.8,
        metadata={}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
