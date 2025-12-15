"""
Unified Scoring Engine v2 (Andy's Methodology)

Combines all scoring factors:
- Fit Score: Business quality signals (reachability, presence)
- Opportunity Score: Marketing gaps + GBP opportunities
- Competition Score: Market saturation
- Industry Multiplier: Niche value weighting

New Formula:
    Priority = (Fit x 0.3 + Opportunity x 0.5 + Competition x 0.2) x Industry Multiplier

Where:
- Fit (30%): Can we reach them?
- Opportunity (50%): Do they need help? (most important)
- Competition (20%): Will we be able to deliver results?
- Industry Multiplier: 0.4x (commoditised) to 1.6x (specialist)
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass

from .fit import calculate_fit_score
from .opportunity import calculate_opportunity_score
from .notes import generate_opportunity_notes
from .competition import calculate_competition_score, get_default_competition, CompetitionAnalysis
from .industry import classify_industry, IndustryClassification


@dataclass
class ProspectScore:
    """Complete prospect scoring result."""
    # Core scores (0-100)
    fit_score: int
    opportunity_score: int
    competition_score: int
    priority_score: int  # Final weighted score

    # Industry classification
    industry_category: str  # commoditised, standard, niche, specialist
    industry_multiplier: float  # 0.4 - 1.6

    # Market context
    market_saturation: str  # low, medium, high, saturated
    franchise_competition: bool

    # GBP-specific
    gbp_has_website: Optional[bool]
    gbp_website_missing_opportunity: bool
    gbp_opportunity_boost: int

    # Human-readable notes
    opportunity_notes: str
    competition_notes: str
    industry_notes: str
    summary: str


def score_prospect(
    prospect: Any,
    search_results: Optional[Dict[str, Any]] = None,
    search_query: str = "",
    search_location: str = "",
) -> ProspectScore:
    """
    Calculate comprehensive prospect score with all factors.

    Args:
        prospect: Prospect object or dict with prospect data
        search_results: Optional raw SerpAPI results for competition analysis
        search_query: Query used to find this prospect (for industry classification)
        search_location: Location searched

    Returns:
        ProspectScore with all scoring components
    """
    # === 1. Fit Score (Business Quality) ===
    fit_score = calculate_fit_score(prospect)

    # === 2. Opportunity Score (Marketing Gaps) ===
    base_opportunity_score = calculate_opportunity_score(prospect)
    opportunity_notes = generate_opportunity_notes(prospect)

    # Add GBP boost if available
    gbp_boost = getattr(prospect, 'gbp_opportunity_boost', 0) or 0
    gbp_notes = getattr(prospect, 'gbp_notes', []) or []

    opportunity_score = min(100, base_opportunity_score + gbp_boost)

    # Prepend GBP notes if present
    if gbp_notes:
        gbp_notes_str = "; ".join(gbp_notes)
        if opportunity_notes:
            opportunity_notes = f"GBP: {gbp_notes_str}; {opportunity_notes}"
        else:
            opportunity_notes = f"GBP: {gbp_notes_str}"

    # === 3. Competition Score (Market Saturation) ===
    if search_results:
        comp_analysis = calculate_competition_score(
            search_results,
            search_query,
            search_location,
        )
    else:
        # Default medium competition if no search context
        comp_analysis = get_default_competition()

    competition_score = comp_analysis.score
    competition_notes = "; ".join(comp_analysis.notes) if comp_analysis.notes else ""

    # === 4. Industry Classification ===
    business_type = search_query or getattr(prospect, 'category', '') or ''
    business_name = getattr(prospect, 'name', '') or ''

    industry_class = classify_industry(business_type, business_name)

    # === 5. Calculate Priority Score ===
    # New weighted formula: (Fit x 0.3 + Opportunity x 0.5 + Competition x 0.2) x Industry Multiplier
    raw_priority = (
        fit_score * 0.30 +      # 30% business quality
        opportunity_score * 0.50 +  # 50% marketing opportunity (most important)
        competition_score * 0.20    # 20% market conditions
    )

    # Apply industry multiplier
    adjusted_priority = raw_priority * industry_class.multiplier

    # Clamp to 0-100
    priority_score = int(max(0, min(100, adjusted_priority)))

    # === 6. Generate Summary ===
    summary = _generate_summary(
        priority_score,
        fit_score,
        opportunity_score,
        comp_analysis,
        industry_class,
        prospect,
    )

    # Extract GBP fields
    gbp_has_website = getattr(prospect, 'gbp_has_website', None)
    gbp_website_missing_opportunity = getattr(prospect, 'gbp_website_missing_opportunity', False) or False

    return ProspectScore(
        fit_score=fit_score,
        opportunity_score=opportunity_score,
        competition_score=competition_score,
        priority_score=priority_score,
        industry_category=industry_class.category,
        industry_multiplier=industry_class.multiplier,
        market_saturation=comp_analysis.saturation,
        franchise_competition=comp_analysis.has_major_franchise,
        gbp_has_website=gbp_has_website,
        gbp_website_missing_opportunity=gbp_website_missing_opportunity,
        gbp_opportunity_boost=gbp_boost,
        opportunity_notes=opportunity_notes,
        competition_notes=competition_notes,
        industry_notes=industry_class.notes,
        summary=summary,
    )


def _generate_summary(
    priority: int,
    fit: int,
    opportunity: int,
    competition: CompetitionAnalysis,
    industry: IndustryClassification,
    prospect: Any,
) -> str:
    """Generate a human-readable scoring summary."""
    parts = []

    # Priority tier
    if priority >= 80:
        parts.append("HOT PROSPECT")
    elif priority >= 60:
        parts.append("High priority")
    elif priority >= 40:
        parts.append("Worth pursuing")
    else:
        parts.append("Lower priority")

    # GBP opportunity (Andy's golden signal)
    gbp_opportunity = getattr(prospect, 'gbp_website_missing_opportunity', False)
    if gbp_opportunity:
        parts.append("Easy win: No website on GBP")

    # Competition context
    if competition.saturation == "low":
        parts.append("Low competition")
    elif competition.saturation == "saturated":
        parts.append("Saturated market")

    # Industry context
    if industry.category == "niche":
        parts.append(f"Niche ({industry.multiplier}x)")
    elif industry.category == "specialist":
        parts.append(f"Specialist ({industry.multiplier}x)")
    elif industry.category == "commoditised":
        parts.append(f"Commoditised ({industry.multiplier}x)")

    # Key opportunity signals
    signals = getattr(prospect, 'signals', None)
    if signals:
        if getattr(signals, 'has_google_analytics', None) is False:
            parts.append("No analytics")
        if getattr(signals, 'has_facebook_pixel', None) is False:
            parts.append("No pixel")

    return "; ".join(parts)


def apply_scores_to_prospect(
    prospect: Any,
    score: ProspectScore,
) -> None:
    """
    Apply calculated scores to a prospect object in place.

    Args:
        prospect: Prospect object to update
        score: ProspectScore with calculated values
    """
    prospect.fit_score = score.fit_score
    prospect.opportunity_score = score.opportunity_score
    prospect.priority_score = score.priority_score
    prospect.opportunity_notes = score.opportunity_notes

    # New Andy's methodology fields
    prospect.competition_score = score.competition_score
    prospect.market_saturation = score.market_saturation
    prospect.franchise_competition = score.franchise_competition
    prospect.industry_category = score.industry_category
    prospect.industry_multiplier = score.industry_multiplier


def calculate_priority_score(
    fit_score: int,
    opportunity_score: int,
    competition_score: int = 50,
    industry_multiplier: float = 1.0,
) -> int:
    """
    Calculate priority score using the new weighted formula.

    Simple helper for cases where you have pre-calculated component scores.

    Args:
        fit_score: Fit score (0-100)
        opportunity_score: Opportunity score (0-100)
        competition_score: Competition score (0-100), default 50
        industry_multiplier: Industry multiplier (0.4-1.6), default 1.0

    Returns:
        Priority score (0-100)
    """
    raw = (
        fit_score * 0.30 +
        opportunity_score * 0.50 +
        competition_score * 0.20
    )
    adjusted = raw * industry_multiplier
    return int(max(0, min(100, adjusted)))
