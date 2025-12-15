"""Database models for prospect persistence."""

import os
import logging
from datetime import datetime
from typing import Optional, List, Generator
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """
    Get database URL based on environment.

    Railway: Uses /data volume for persistence (if mounted)
    Fallback: Uses /app/data for Railway without volume
    Local: Uses ./prospects.db in project root
    """
    # Check for explicit DATABASE_URL first (allows override)
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    # Check for Railway environment
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        # Try /data first (persistent volume mount point)
        if os.path.exists("/data") and os.access("/data", os.W_OK):
            return "sqlite:////data/prospects.db"

        # Fallback to /app/data (within the app directory)
        # This won't persist across deploys but allows the app to start
        os.makedirs("/app/data", exist_ok=True)
        return "sqlite:////app/data/prospects.db"

    # Local development
    return "sqlite:///./prospects.db"


DATABASE_URL = get_database_url()

# Handle SQLite-specific settings
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SearchConfig(Base):
    """
    Search depth configuration.

    Defines tiered search depths for controlling API usage and prospect coverage.
    """
    __tablename__ = "search_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # quick, standard, deep, exhaustive
    description = Column(String(255))

    # Pagination
    organic_pages = Column(Integer, default=1)  # How many pages of organic results
    maps_pages = Column(Integer, default=1)     # How many pages of maps results

    # Query expansion
    use_query_variations = Column(Boolean, default=False)
    query_variations = Column(JSON, default=[])  # Additional query templates

    # Location expansion
    use_location_expansion = Column(Boolean, default=False)
    expansion_radius_km = Column(Integer, default=0)  # 0 = no expansion
    max_locations = Column(Integer, default=1)

    # Search types
    search_organic = Column(Boolean, default=True)
    search_maps = Column(Boolean, default=True)
    search_local_services = Column(Boolean, default=False)

    # Cost controls
    max_api_calls = Column(Integer, default=5)
    estimated_cost_cents = Column(Integer, default=5)


class Campaign(Base):
    """Saved search campaign - reusable search configuration."""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    business_type = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    limit = Column(Integer, default=20)
    filters = Column(JSON, default={})

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)

    # Color/icon for UI
    color = Column(String(20), default="blue")
    icon = Column(String(50), default="search")

    # Relationships
    searches = relationship("Search", back_populates="campaign")

    def __repr__(self):
        return f"<Campaign {self.name}: {self.business_type} in {self.location}>"


class Search(Base):
    """Individual search run - snapshot of results at a point in time."""
    __tablename__ = "searches"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)

    # Search parameters
    business_type = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    query = Column(String(500))

    # Results summary
    total_found = Column(Integer, default=0)
    avg_fit_score = Column(Float, default=0)
    avg_opportunity_score = Column(Float, default=0)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Integer, nullable=True)

    # Status
    status = Column(String(20), default="pending")  # pending, running, complete, error
    error = Column(Text, nullable=True)

    # Search depth tracking
    config_name = Column(String(50), default="standard")  # quick, standard, deep, exhaustive
    api_calls_made = Column(Integer, default=0)
    api_calls_budget = Column(Integer, default=5)
    actual_cost_cents = Column(Integer, default=0)

    # Expansion tracking
    queries_searched = Column(JSON, default=[])  # All query variations used
    locations_searched = Column(JSON, default=[])  # All locations searched
    pages_fetched = Column(JSON, default={})  # {"organic": [1,2,3], "maps": [1]}

    # Results by source
    results_from_organic = Column(Integer, default=0)
    results_from_maps = Column(Integer, default=0)
    results_from_ads = Column(Integer, default=0)

    # Relationships
    campaign = relationship("Campaign", back_populates="searches")
    prospects = relationship("Prospect", back_populates="search", cascade="all, delete-orphan")


class Prospect(Base):
    """Individual prospect - persisted across searches for tracking."""
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("searches.id"))

    # Identity (used for deduplication across searches)
    domain = Column(String(255), index=True)
    name = Column(String(255))

    # Contact
    website = Column(String(500))
    phone = Column(String(50))
    emails = Column(Text)  # JSON array or comma-separated
    address = Column(String(500))

    # Google data
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)

    # SERP presence
    found_in_ads = Column(Boolean, default=False)
    found_in_maps = Column(Boolean, default=False)
    found_in_organic = Column(Boolean, default=False)
    organic_position = Column(Integer, nullable=True)
    maps_position = Column(Integer, nullable=True)

    # Enrichment
    cms = Column(String(50))
    has_analytics = Column(Boolean, default=False)
    has_facebook_pixel = Column(Boolean, default=False)
    has_booking = Column(Boolean, default=False)
    load_time_ms = Column(Integer, nullable=True)

    # Scores
    fit_score = Column(Integer, default=0)
    opportunity_score = Column(Integer, default=0)
    priority_score = Column(Float, default=0)
    opportunity_notes = Column(Text)

    # Competition & Market Context (Andy's Methodology)
    competition_score = Column(Integer, default=50)  # 0-100, higher = less competition
    market_saturation = Column(String(20), default="medium")  # low, medium, high, saturated
    franchise_competition = Column(Boolean, default=False)
    ads_in_market = Column(Integer, default=0)

    # Industry Classification
    industry_category = Column(String(20), default="standard")  # commoditised, standard, niche, specialist
    industry_multiplier = Column(Float, default=1.0)  # 0.4 - 1.6

    # GBP-specific Signals
    gbp_has_website = Column(Boolean, default=None)  # None = not from Maps, True/False = detected
    gbp_website_missing_opportunity = Column(Boolean, default=False)  # Good reviews + no website

    # User workflow
    status = Column(String(20), default="new")  # new, qualified, contacted, meeting, won, lost, skipped
    user_notes = Column(Text)
    contacted_at = Column(DateTime, nullable=True)
    follow_up_at = Column(DateTime, nullable=True)

    # Metadata
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    seen_count = Column(Integer, default=1)

    # Tags (JSON array)
    tags = Column(JSON, default=[])

    # Relationships
    search = relationship("Search", back_populates="prospects")

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "search_id": self.search_id,
            "domain": self.domain,
            "name": self.name,
            "website": self.website,
            "phone": self.phone,
            "emails": self.emails,
            "address": self.address,
            "rating": self.rating,
            "review_count": self.review_count,
            "found_in_ads": self.found_in_ads,
            "found_in_maps": self.found_in_maps,
            "found_in_organic": self.found_in_organic,
            "organic_position": self.organic_position,
            "maps_position": self.maps_position,
            "cms": self.cms,
            "has_analytics": self.has_analytics,
            "has_facebook_pixel": self.has_facebook_pixel,
            "has_booking": self.has_booking,
            "load_time_ms": self.load_time_ms,
            "fit_score": self.fit_score,
            "opportunity_score": self.opportunity_score,
            "priority_score": self.priority_score,
            "opportunity_notes": self.opportunity_notes,
            # Competition & Market
            "competition_score": self.competition_score,
            "market_saturation": self.market_saturation,
            "franchise_competition": self.franchise_competition,
            "ads_in_market": self.ads_in_market,
            # Industry
            "industry_category": self.industry_category,
            "industry_multiplier": self.industry_multiplier,
            # GBP
            "gbp_has_website": self.gbp_has_website,
            "gbp_website_missing_opportunity": self.gbp_website_missing_opportunity,
            "status": self.status,
            "user_notes": self.user_notes,
            "contacted_at": self.contacted_at.isoformat() if self.contacted_at else None,
            "follow_up_at": self.follow_up_at.isoformat() if self.follow_up_at else None,
            "first_seen_at": self.first_seen_at.isoformat() if self.first_seen_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "seen_count": self.seen_count,
            "tags": self.tags or [],
        }


class Tag(Base):
    """User-defined tags for organizing prospects."""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(20), default="gray")
    created_at = Column(DateTime, default=datetime.utcnow)


class ExportHistory(Base):
    """Track exports for audit trail."""
    __tablename__ = "export_history"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("searches.id"), nullable=True)

    export_type = Column(String(20))  # csv, json, sheets
    record_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # For Sheets exports
    sheet_url = Column(String(500), nullable=True)


class SearchMetrics(Base):
    """
    Cache competition metrics per query/location.

    Stores market analysis that can be reused across prospects
    from the same search to avoid recalculating.
    """
    __tablename__ = "search_metrics"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)

    # Competition data from search results
    organic_count = Column(Integer, default=0)
    maps_count = Column(Integer, default=0)
    ads_count = Column(Integer, default=0)

    # Calculated competition score
    competition_score = Column(Integer, default=50)  # 0-100, higher = less competition
    market_saturation = Column(String(20))  # low, medium, high, saturated

    # Franchise detection
    franchises_detected = Column(Text, default="[]")  # JSON array of franchise names
    has_major_franchise = Column(Boolean, default=False)

    # Industry classification for this query
    industry_category = Column(String(20))  # commoditised, standard, niche, specialist
    industry_multiplier = Column(Float, default=1.0)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint on query + location
    __table_args__ = (
        UniqueConstraint('query', 'location', name='uq_search_metrics_query_location'),
    )


def seed_search_configs(db: Session) -> None:
    """Seed default search configurations."""
    configs = [
        {
            "name": "quick",
            "description": "Fast scan - first page only",
            "organic_pages": 1,
            "maps_pages": 0,
            "use_query_variations": False,
            "use_location_expansion": False,
            "search_organic": True,
            "search_maps": True,
            "search_local_services": False,
            "max_api_calls": 1,
            "estimated_cost_cents": 1,
        },
        {
            "name": "standard",
            "description": "Balanced search - good coverage",
            "organic_pages": 2,
            "maps_pages": 1,
            "use_query_variations": True,
            "query_variations": ["{business_type} services", "{business_type} near me"],
            "use_location_expansion": False,
            "search_organic": True,
            "search_maps": True,
            "search_local_services": False,
            "max_api_calls": 5,
            "estimated_cost_cents": 5,
        },
        {
            "name": "deep",
            "description": "Comprehensive - multiple queries and locations",
            "organic_pages": 3,
            "maps_pages": 2,
            "use_query_variations": True,
            "query_variations": [
                "{business_type} services",
                "{business_type} near me",
                "best {business_type}",
                "local {business_type}",
            ],
            "use_location_expansion": True,
            "expansion_radius_km": 10,
            "max_locations": 5,
            "search_organic": True,
            "search_maps": True,
            "search_local_services": True,
            "max_api_calls": 20,
            "estimated_cost_cents": 15,
        },
        {
            "name": "exhaustive",
            "description": "Full market mapping - maximum coverage",
            "organic_pages": 5,
            "maps_pages": 3,
            "use_query_variations": True,
            "query_variations": [
                "{business_type} services",
                "{business_type} near me",
                "best {business_type}",
                "local {business_type}",
                "emergency {business_type}",
                "cheap {business_type}",
                "24 hour {business_type}",
                "{business_type} company",
            ],
            "use_location_expansion": True,
            "expansion_radius_km": 25,
            "max_locations": 10,
            "search_organic": True,
            "search_maps": True,
            "search_local_services": True,
            "max_api_calls": 50,
            "estimated_cost_cents": 40,
        },
    ]

    for config in configs:
        existing = db.query(SearchConfig).filter(SearchConfig.name == config["name"]).first()
        if not existing:
            db.add(SearchConfig(**config))

    db.commit()
    logger.debug("Search configs seeded")


def init_db():
    """Initialize database tables and seed data."""
    Base.metadata.create_all(bind=engine)

    # Seed search configs
    db = SessionLocal()
    try:
        seed_search_configs(db)
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_prospects_from_results(db: Session, search_id: int, results: list) -> List[Prospect]:
    """
    Save prospect results to database.

    Converts search results (Prospect model from models.py) to database Prospect records.
    Includes Andy's methodology fields (competition, industry, GBP).
    """
    prospects = []
    for r in results:
        # Extract emails as comma-separated string
        emails = ",".join(r.emails) if r.emails else None

        prospect = Prospect(
            search_id=search_id,
            domain=r.domain,
            name=r.name,
            website=r.website,
            phone=r.phone,
            emails=emails,
            address=r.address,
            rating=r.rating,
            review_count=r.review_count,
            found_in_ads=r.found_in_ads,
            found_in_maps=r.found_in_maps,
            found_in_organic=r.found_in_organic,
            organic_position=r.organic_position,
            maps_position=r.maps_position,
            cms=r.signals.cms if r.signals else None,
            has_analytics=r.signals.has_google_analytics if r.signals else False,
            has_facebook_pixel=r.signals.has_facebook_pixel if r.signals else False,
            has_booking=r.signals.has_booking_system if r.signals else False,
            load_time_ms=r.signals.load_time_ms if r.signals else None,
            fit_score=r.fit_score,
            opportunity_score=r.opportunity_score,
            priority_score=r.priority_score,
            opportunity_notes=r.opportunity_notes,
            # Andy's methodology fields
            competition_score=getattr(r, 'competition_score', 50),
            market_saturation=getattr(r, 'market_saturation', 'medium'),
            franchise_competition=getattr(r, 'franchise_competition', False),
            ads_in_market=getattr(r, 'ads_in_market', 0),
            industry_category=getattr(r, 'industry_category', 'standard'),
            industry_multiplier=getattr(r, 'industry_multiplier', 1.0),
            gbp_has_website=getattr(r, 'gbp_has_website', None),
            gbp_website_missing_opportunity=getattr(r, 'gbp_website_missing_opportunity', False),
        )
        db.add(prospect)
        prospects.append(prospect)

    db.commit()
    return prospects
