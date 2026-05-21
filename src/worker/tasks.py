import asyncio
import logging
from celery import chain, group, chord
from .celery_app import celery_app
from src.agents.scraper import ScraperAgent
from src.agents.vision import VisionAnalysisAgent
from src.agents.psychology import PsychologyAnalysisAgent
from src.db.database import SessionLocal
from src.db import models
from src.embeddings.embedder import get_embedder
from src.db.vector_db import upsert_vector

logger = logging.getLogger(__name__)


# ============= INDIVIDUAL AGENT TASKS =============

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def crawl_platform_task(self, platform: str, brand: str = None):
    """
    Celery task to trigger the ScraperAgent for platform crawling.
    
    Args:
        platform: Platform to crawl (facebook, google, etc.)
        brand: Optional brand to filter by
    
    Returns:
        List of crawled ads
    """
    try:
        logger.info(f"Starting crawl for {platform} - {brand}")
        scraper = ScraperAgent()
        results = asyncio.run(scraper.crawl_platform(platform, brand))
        logger.info(f"Crawl completed: {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Crawl failed: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_vision_task(self, image_url: str, creative_id: int = None):
    """
    Celery task to run visual analysis on an image.
    
    Args:
        image_url: URL of the image to analyze
        creative_id: Optional creative ID for database linking
    
    Returns:
        Vision analysis results
    """
    try:
        logger.info(f"Starting vision analysis for {image_url}")
        vision_agent = VisionAnalysisAgent()
        results = vision_agent.analyze_image(image_url)
        
        # Store results if creative_id provided
        if creative_id:
            db = SessionLocal()
            try:
                analysis = db.query(models.AnalysisResults).filter(
                    models.AnalysisResults.ad_id == creative_id
                ).first()
                
                if analysis:
                    analysis.vision_tags = results.get("tags", [])
                    analysis.color_palette = results.get("color_palette", [])
                    analysis.detected_objects = results.get("detected_objects", [])
                    analysis.ocr_text = results.get("ocr_text")
                    db.commit()
                    logger.info(f"Stored vision analysis for creative {creative_id}")
            except Exception as db_error:
                logger.error(f"Error storing vision results: {db_error}")
                db.rollback()
            finally:
                db.close()
        
        return results
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_psychology_task(self, copy_text: str, ad_id: int = None):
    """
    Celery task to run marketing psychology analysis.
    
    Args:
        copy_text: Marketing copy to analyze
        ad_id: Optional ad ID for database linking
    
    Returns:
        Psychology analysis results
    """
    try:
        logger.info(f"Starting psychology analysis for ad {ad_id}")
        psych_agent = PsychologyAnalysisAgent()
        results = psych_agent.analyze_copy(copy_text)
        
        # Store results if ad_id provided
        if ad_id:
            db = SessionLocal()
            try:
                analysis = db.query(models.AnalysisResults).filter(
                    models.AnalysisResults.ad_id == ad_id
                ).first()
                
                if analysis:
                    analysis.psychology_classification = results.get("classification")
                    analysis.emotional_triggers = results.get("emotional_triggers", [])
                    analysis.pain_points = results.get("pain_points", [])
                    analysis.raw_analysis = results.get("raw_analysis")
                    db.commit()
                    logger.info(f"Stored psychology analysis for ad {ad_id}")
            except Exception as db_error:
                logger.error(f"Error storing psychology results: {db_error}")
                db.rollback()
            finally:
                db.close()
        
        return results
    except Exception as e:
        logger.error(f"Psychology analysis failed: {e}")
        raise self.retry(exc=e, countdown=60)


# ============= ORCHESTRATION TASKS =============

@celery_app.task(bind=True)
def aggregate_analysis_results(self, vision_results, psychology_results, ad_id: int):
    """
    Aggregate results from multiple analysis tasks.
    
    Args:
        vision_results: Results from vision analysis
        psychology_results: Results from psychology analysis
        ad_id: ID of the ad being analyzed
    
    Returns:
        Aggregated results
    """
    try:
        logger.info(f"Aggregating analysis results for ad {ad_id}")
        
        db = SessionLocal()
        try:
            # Get or create analysis record
            analysis = db.query(models.AnalysisResults).filter(
                models.AnalysisResults.ad_id == ad_id
            ).first()
            
            if not analysis:
                analysis = models.AnalysisResults(ad_id=ad_id)
                db.add(analysis)
            
            # Update with aggregated results
            if vision_results:
                analysis.vision_tags = vision_results.get("tags")
                analysis.color_palette = vision_results.get("color_palette")
                analysis.detected_objects = vision_results.get("detected_objects")
                analysis.ocr_text = vision_results.get("ocr_text")
            
            if psychology_results:
                analysis.psychology_classification = psychology_results.get("classification")
                analysis.emotional_triggers = psychology_results.get("emotional_triggers")
                analysis.pain_points = psychology_results.get("pain_points")
            
            db.commit()
            logger.info(f"Aggregated analysis for ad {ad_id}")
            return {"status": "completed", "ad_id": ad_id}
        except Exception as db_error:
            logger.error(f"Error aggregating results: {db_error}")
            db.rollback()
            raise
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise


def orchestrate_full_analysis(ad_id: int, image_urls: list = None, copy_text: str = None):
    """
    Create a task chain for end-to-end analysis.
    Chains vision analysis -> psychology analysis -> aggregation.
    
    Args:
        ad_id: ID of ad to analyze
        image_urls: List of image URLs to analyze
        copy_text: Marketing copy to analyze
    
    Returns:
        Celery AsyncResult
    """
    logger.info(f"Orchestrating full analysis for ad {ad_id}")
    
    tasks = []
    
    if image_urls:
        for image_url in image_urls:
            tasks.append(analyze_vision_task.s(image_url, ad_id))
    
    if copy_text:
        tasks.append(analyze_psychology_task.s(copy_text, ad_id))
    
    if not tasks:
        logger.warning(f"No analysis tasks for ad {ad_id}")
        return None
    
    # Chain all tasks
    workflow = chain(
        group(*tasks) if len(tasks) > 1 else tasks[0],
        aggregate_analysis_results.s(ad_id)
    )
    
    return workflow.apply_async()


@celery_app.task
def bulk_embed_creatives(creative_ids: list):
    """
    Bulk generate embeddings for multiple creatives.
    
    Args:
        creative_ids: List of creative IDs
    
    Returns:
        Number of embeddings generated
    """
    logger.info(f"Generating embeddings for {len(creative_ids)} creatives")
    
    db = SessionLocal()
    embedder = get_embedder()
    count = 0
    
    try:
        for creative_id in creative_ids:
            creative = db.query(models.Creatives).get(creative_id)
            if creative and not creative.embedding:
                # Generate embedding
                embedding = embedder.embed_ad_creative(
                    headline=creative.headline or "",
                    caption=creative.caption or "",
                    cta=creative.cta_text or ""
                )
                
                # Store in database
                creative.embedding = embedding
                
                # Upsert to vector store
                ad = db.query(models.Ads).get(creative.ad_id)
                upsert_vector(
                    point_id=creative.id,
                    vector=embedding,
                    payload={
                        "creative_id": creative.id,
                        "ad_id": creative.ad_id,
                        "brand_name": ad.brand_name if ad else "Unknown",
                        "platform": ad.platform if ad else "Unknown",
                    }
                )
                
                count += 1
                
                if count % 10 == 0:
                    db.commit()
                    logger.info(f"Processed {count} creatives")
        
        db.commit()
        logger.info(f"Generated {count} embeddings")
        return {"status": "completed", "count": count}
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        db.rollback()
        raise
    finally:
        db.close()
