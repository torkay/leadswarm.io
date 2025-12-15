"""Data models for the prospect scraper."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class AdResult:
    """Represents a Google Ads result from SERP."""

    position: int
    headline: str
    display_url: str
    destination_url: str
    description: str
    is_top: bool  # True if ad is above organic results


@dataclass
class MapsResult:
    """Represents a Google Maps/Local Pack result from SERP."""

    position: int
    name: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    category: Optional[str] = None
    address: str = ""
    phone: Optional[str] = None
    website: Optional[str] = None

    # GBP-specific detection (Andy's methodology)
    gbp_has_website: Optional[bool] = None  # None = unknown, True/False = detected
    gbp_website_missing_opportunity: bool = False  # Good reviews + no website = easy sell
    gbp_opportunity_boost: int = 0  # Extra points to add to opportunity score
    gbp_notes: list = field(default_factory=list)  # Human-readable GBP opportunity notes


@dataclass
class OrganicResult:
    """Represents an organic search result from SERP."""

    position: int
    title: str
    url: str
    domain: str
    snippet: str


@dataclass
class SerpResults:
    """Container for all SERP results from a single search."""

    query: str
    location: str
    timestamp: datetime = field(default_factory=datetime.now)
    ads: list[AdResult] = field(default_factory=list)
    maps: list[MapsResult] = field(default_factory=list)
    organic: list[OrganicResult] = field(default_factory=list)

    def to_competition_dict(self) -> dict:
        """
        Convert to dict format expected by calculate_competition_score().

        Returns dict with keys: ads, organic_results, local_results
        """
        return {
            "ads": [
                {
                    "position": ad.position,
                    "title": ad.headline,
                    "displayed_link": ad.display_url,
                    "link": ad.destination_url,
                    "description": ad.description,
                    "block_position": "top" if ad.is_top else "bottom",
                }
                for ad in self.ads
            ],
            "organic_results": [
                {
                    "position": org.position,
                    "title": org.title,
                    "link": org.url,
                    "displayed_link": org.domain,
                    "snippet": org.snippet,
                }
                for org in self.organic
            ],
            "local_results": {
                "places": [
                    {
                        "position": m.position,
                        "title": m.name,
                        "rating": m.rating,
                        "reviews": m.review_count,
                        "type": m.category,
                        "address": m.address,
                        "phone": m.phone,
                        "website": m.website,
                    }
                    for m in self.maps
                ]
            },
            "local_ads": [],  # Local services not typically in SerpResults
        }


@dataclass
class WebsiteSignals:
    """
    Marketing signals extracted from a website.

    IMPORTANT: None means "unknown", not "missing".
    - None = couldn't determine (timeout, blocked, etc.)
    - True = confirmed present
    - False = confirmed absent
    """

    url: str
    reachable: bool = False
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    cms: Optional[str] = None
    # Tracking - None = unknown, True = present, False = absent
    has_google_analytics: Optional[bool] = None
    has_facebook_pixel: Optional[bool] = None
    has_google_ads: Optional[bool] = None
    has_booking_system: Optional[bool] = None
    load_time_ms: Optional[int] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    social_links: list[str] = field(default_factory=list)


@dataclass
class Prospect:
    """A potential prospect/lead with all gathered data."""

    name: str
    website: Optional[str] = None
    domain: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    # SERP presence
    found_in_ads: bool = False
    ad_position: Optional[int] = None
    found_in_maps: bool = False
    maps_position: Optional[int] = None
    found_in_organic: bool = False
    organic_position: Optional[int] = None

    # Google Business Profile data
    rating: Optional[float] = None
    review_count: Optional[int] = None
    category: Optional[str] = None

    # Contact info
    emails: list[str] = field(default_factory=list)

    # Website signals
    signals: Optional[WebsiteSignals] = None

    # Scores
    fit_score: int = 0
    opportunity_score: int = 0
    priority_score: float = 0.0
    opportunity_notes: str = ""

    # Competition & Market Context (Andy's methodology)
    competition_score: int = 50  # 0-100, higher = less competition
    market_saturation: str = "medium"  # low, medium, high, saturated
    franchise_competition: bool = False
    ads_in_market: int = 0

    # Industry Classification
    industry_category: str = "standard"  # commoditised, standard, niche, specialist
    industry_multiplier: float = 1.0  # 0.4 - 1.6

    # GBP-specific Signals
    gbp_has_website: Optional[bool] = None  # None = not from Maps
    gbp_website_missing_opportunity: bool = False  # Good reviews + no website
    gbp_opportunity_boost: int = 0  # Extra points for opportunity score
    gbp_notes: list = field(default_factory=list)

    # Metadata
    source: str = ""  # Where this prospect was first found
    scraped_at: datetime = field(default_factory=datetime.now)

    def merge_from(self, other: "Prospect") -> None:
        """Merge data from another prospect record (for deduplication)."""
        # Keep existing values, fill in missing ones
        if not self.website and other.website:
            self.website = other.website
            self.domain = other.domain
        if not self.phone and other.phone:
            self.phone = other.phone
        if not self.address and other.address:
            self.address = other.address
        if not self.rating and other.rating:
            self.rating = other.rating
        if not self.review_count and other.review_count:
            self.review_count = other.review_count
        if not self.category and other.category:
            self.category = other.category

        # Merge SERP presence
        if other.found_in_ads:
            self.found_in_ads = True
            if not self.ad_position or other.ad_position < self.ad_position:
                self.ad_position = other.ad_position
        if other.found_in_maps:
            self.found_in_maps = True
            if not self.maps_position or other.maps_position < self.maps_position:
                self.maps_position = other.maps_position
        if other.found_in_organic:
            self.found_in_organic = True
            if not self.organic_position or other.organic_position < self.organic_position:
                self.organic_position = other.organic_position

        # Merge emails (unique)
        for email in other.emails:
            if email not in self.emails:
                self.emails.append(email)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = {
            "name": self.name,
            "website": self.website,
            "domain": self.domain,
            "phone": self.phone,
            "address": self.address,
            "emails": self.emails or [],
            "rating": self.rating,
            "review_count": self.review_count,
            "category": self.category,
            "found_in_ads": self.found_in_ads,
            "ad_position": self.ad_position,
            "found_in_maps": self.found_in_maps,
            "maps_position": self.maps_position,
            "found_in_organic": self.found_in_organic,
            "organic_position": self.organic_position,
            "fit_score": self.fit_score,
            "opportunity_score": self.opportunity_score,
            "priority_score": round(self.priority_score, 2),
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
            "gbp_opportunity_boost": self.gbp_opportunity_boost,
            "gbp_notes": self.gbp_notes,
            "source": self.source,
        }

        # Add signals if available
        if self.signals:
            data["signals"] = {
                "reachable": self.signals.reachable,
                "cms": self.signals.cms,
                "has_google_analytics": self.signals.has_google_analytics,
                "has_facebook_pixel": self.signals.has_facebook_pixel,
                "has_google_ads": self.signals.has_google_ads,
                "has_booking_system": self.signals.has_booking_system,
                "load_time_ms": self.signals.load_time_ms,
            }

        return data


@dataclass
class CrawlResult:
    """Result from crawling a website."""

    url: str
    success: bool
    html: str = ""
    load_time_ms: int = 0
    status_code: Optional[int] = None
    error: Optional[str] = None
    final_url: Optional[str] = None  # After redirects
