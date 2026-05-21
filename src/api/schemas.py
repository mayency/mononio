from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============= AD SCHEMAS =============

class AdBase(BaseModel):
    """Base schema for Ad creation/updates."""
    platform: str = Field(..., description="Advertising platform (facebook, instagram, google, etc.)")
    advertiser_id: str = Field(..., description="ID of the advertiser")
    brand_name: str = Field(..., description="Brand name")
    is_active: bool = Field(default=True, description="Whether the ad is currently active")
    start_date: datetime = Field(..., description="When the ad campaign started")
    end_date: Optional[datetime] = Field(default=None, description="When the ad campaign ended")


class AdCreate(AdBase):
    """Schema for creating a new ad."""
    pass


class AdResponse(AdBase):
    """Schema for returning ad data from API."""
    id: int
    active_days: int = Field(..., description="Number of days the ad has been active")
    longevity_score: float = Field(..., description="Score indicating ad longevity/success")
    created_at: datetime
    updated_at: datetime
    
    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True)


# ============= CREATIVE SCHEMAS =============

class CreativeBase(BaseModel):
    """Base schema for Creative assets."""
    ad_id: int
    media_type: str = Field(..., description="Type of media (image, video, carousel)")
    media_url: str = Field(..., description="URL to the media asset")
    headline: Optional[str] = Field(default=None, description="Ad headline")
    caption: Optional[str] = Field(default=None, description="Ad caption/body text")
    cta_text: Optional[str] = Field(default=None, description="Call-to-action text")
    landing_page_url: Optional[str] = Field(default=None, description="Landing page URL")


class CreativeCreate(CreativeBase):
    """Schema for creating a new creative."""
    pass


class CreativeResponse(CreativeBase):
    """Schema for returning creative data."""
    id: int
    embedding: Optional[List[float]] = Field(default=None, description="Semantic embedding vector")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= ANALYSIS SCHEMAS =============

class AnalysisResultsBase(BaseModel):
    """Base schema for analysis results."""
    ad_id: int
    vision_tags: Optional[Dict[str, Any]] = Field(default=None, description="Vision analysis tags")
    color_palette: Optional[List[str]] = Field(default=None, description="Dominant colors detected")
    detected_objects: Optional[List[str]] = Field(default=None, description="Objects detected in image")
    ocr_text: Optional[str] = Field(default=None, description="Text extracted from image")
    psychology_classification: Optional[str] = Field(default=None, description="Psychology classification")
    emotional_triggers: Optional[List[str]] = Field(default=None, description="Detected emotional triggers")
    pain_points: Optional[List[str]] = Field(default=None, description="Identified pain points")
    audience_inference: Optional[Dict[str, Any]] = Field(default=None, description="Inferred audience data")
    estimated_ctr: Optional[float] = Field(default=None, description="Estimated click-through rate")
    raw_analysis: Optional[str] = Field(default=None, description="Raw LLM analysis response")


class AnalysisResultsCreate(AnalysisResultsBase):
    """Schema for creating analysis results."""
    pass


class AnalysisResultsResponse(AnalysisResultsBase):
    """Schema for returning analysis results."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= SEARCH SCHEMAS =============

class SearchQuery(BaseModel):
    """Schema for semantic search queries."""
    query_text: str = Field(..., description="Text to search for")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters (platform, brand, etc.)")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")


class SearchResultItem(BaseModel):
    """Individual search result item."""
    creative_id: int = Field(..., description="ID of the matching creative")
    ad_id: int = Field(..., description="ID of the associated ad")
    score: float = Field(..., description="Similarity score (0-1)")
    brand_name: str = Field(..., description="Brand name")
    platform: str = Field(..., description="Platform")
    headline: Optional[str] = Field(default=None, description="Ad headline")
    media_url: Optional[str] = Field(default=None, description="Media URL")


class SearchResponse(BaseModel):
    """Response for search queries."""
    query: str = Field(..., description="Original query text")
    results: List[SearchResultItem] = Field(..., description="Matching results")
    total: int = Field(..., description="Total number of results")


# ============= AGENT QUERY SCHEMAS =============

class AgentQuery(BaseModel):
    """Schema for querying the marketing intelligence brain."""
    query: str = Field(..., description="Natural language query")
    agent_type: Optional[str] = Field(default="general", description="Type of agent (scraper, vision, psychology, general)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class AgentResponse(BaseModel):
    """Schema for agent query responses."""
    query: str
    agent_type: str
    response: str
    confidence: Optional[float] = Field(default=None, description="Confidence score")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


# ============= BATCH OPERATIONS SCHEMAS =============

class BatchAnalysisRequest(BaseModel):
    """Request schema for batch analysis operations."""
    ad_ids: List[int] = Field(..., description="List of ad IDs to analyze")
    analysis_types: List[str] = Field(default=["vision", "psychology"], description="Types of analysis to run")
    priority: str = Field(default="normal", description="Task priority (low, normal, high)")


class BatchAnalysisResponse(BaseModel):
    """Response for batch analysis operations."""
    batch_id: str = Field(..., description="Unique batch operation ID")
    status: str = Field(..., description="Current status (queued, processing, completed)")
    total_ads: int = Field(..., description="Total ads in batch")
    processed: int = Field(default=0, description="Number processed so far")
    created_at: datetime
