from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import json


class Ads(Base):
    """Model representing advertising campaigns."""
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, index=True, nullable=False)  # facebook, instagram, google, etc.
    advertiser_id = Column(String, index=True, nullable=False)
    brand_name = Column(String, index=True, nullable=False)
    active_days = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    longevity_score = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creatives = relationship("Creatives", back_populates="ad", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResults", back_populates="ad", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ads(id={self.id}, brand={self.brand_name}, platform={self.platform})>"


class Creatives(Base):
    """Model representing ad creative assets (images, videos, copy)."""
    __tablename__ = "creatives"

    id = Column(Integer, primary_key=True, index=True)
    ad_id = Column(Integer, ForeignKey("ads.id", ondelete="CASCADE"), nullable=False)
    media_type = Column(String, nullable=False)  # image, video, carousel
    media_url = Column(String, nullable=False)
    headline = Column(Text, nullable=True)
    caption = Column(Text, nullable=True)
    cta_text = Column(String, nullable=True)  # Call-to-Action text
    landing_page_url = Column(String, nullable=True)
    
    # Vector embedding for semantic search (stored as JSON)
    embedding = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    ad = relationship("Ads", back_populates="creatives")

    def __repr__(self):
        return f"<Creatives(id={self.id}, ad_id={self.ad_id}, media_type={self.media_type})>"


class AnalysisResults(Base):
    """Model storing results from vision, psychology, and NLP analysis agents."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    ad_id = Column(Integer, ForeignKey("ads.id", ondelete="CASCADE"), nullable=False)
    
    # Vision analysis results (stored as JSON)
    vision_tags = Column(JSON, nullable=True)  # Objects detected, colors, composition
    color_palette = Column(JSON, nullable=True)  # Dominant colors
    detected_objects = Column(JSON, nullable=True)  # YOLO/CV detected objects
    ocr_text = Column(Text, nullable=True)  # Text extracted from image
    
    # Psychology analysis results
    psychology_classification = Column(String, nullable=True)  # e.g., "emotional", "rational", "urgency-driven"
    emotional_triggers = Column(JSON, nullable=True)  # List of detected emotional triggers
    pain_points = Column(JSON, nullable=True)  # Identified pain points
    
    # Audience inference
    audience_inference = Column(JSON, nullable=True)  # Inferred target demographic
    estimated_ctr = Column(Float, nullable=True)  # Predicted click-through rate
    
    # Raw analysis response
    raw_analysis = Column(Text, nullable=True)  # Full LLM response
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    ad = relationship("Ads", back_populates="analysis_results")

    def __repr__(self):
        return f"<AnalysisResults(id={self.id}, ad_id={self.ad_id})>"
