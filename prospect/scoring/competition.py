"""
Competition Score Calculator

Analyses search results to determine market saturation.
Lower competition = Higher opportunity for client success.

Score: 0-100 where HIGHER = LESS competition (better opportunity):
- 0-25: Saturated (many ads, franchises, full organic)
- 26-50: High competition
- 51-75: Medium competition
- 76-100: Low competition (ideal)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class CompetitionAnalysis:
    """Results of competition analysis."""
    score: int  # 0-100, higher = less competition
    saturation: str  # low, medium, high, saturated
    ads_count: int
    organic_count: int
    maps_count: int
    franchises_found: List[str]
    has_major_franchise: bool
    notes: List[str]


# Major franchises that indicate saturated markets
FRANCHISE_PATTERNS: Dict[str, str] = {
    # Home services franchises
    "jim's": "Jim's Group",
    "hire a hubby": "Hire A Hubby",
    "fantastic": "Fantastic Services",
    "dyno": "Dyno",
    "metropolitan plumbing": "Metropolitan Plumbing",
    "fallon": "Fallon Solutions",
    "mr splash": "Mr Splash Plumbing",
    "same day": "Same Day",
    "service today": "Service Today",

    # Real estate franchises
    "mcgrath": "McGrath",
    "ray white": "Ray White",
    "lj hooker": "LJ Hooker",
    "harcourts": "Harcourts",
    "century 21": "Century 21",
    "belle property": "Belle Property",
    "raine & horne": "Raine & Horne",
    "barry plant": "Barry Plant",
    "jellis craig": "Jellis Craig",

    # Cleaning franchises
    "merry maids": "Merry Maids",
    "molly maid": "Molly Maid",
    "absolute domestics": "Absolute Domestics",
    "home clean heroes": "Home Clean Heroes",

    # Automotive franchises
    "ultra tune": "Ultra Tune",
    "midas": "Midas",
    "kmart tyre": "Kmart Tyre & Auto",
    "beaurepaires": "Beaurepaires",
    "jax": "JAX Tyres",
    "mycar": "mycar",

    # Other service franchises
    "snap fitness": "Snap Fitness",
    "anytime fitness": "Anytime Fitness",
    "f45": "F45 Training",
}

# Directory sites to exclude from organic competition count
DIRECTORY_DOMAINS = {
    "yellowpages", "truelocal", "hotfrog", "localsearch",
    "yelp", "airtasker", "hipages", "serviceseeking", "oneflare",
    "productreview", "wordofmouth", "brownbook", "cylex",
    "whitepages", "whereis", "startlocal", "businesslistings",
    "infobel", "aussieweb", "dlook", "localstore",
}


def calculate_competition_score(
    search_results: Dict[str, Any],
    query: str = "",
    location: str = "",
) -> CompetitionAnalysis:
    """
    Analyse search results to calculate competition score.

    Args:
        search_results: Raw SerpAPI response or similar structure
        query: Search query used
        location: Location searched

    Returns:
        CompetitionAnalysis with score and breakdown
    """
    notes = []

    # Extract result counts from various possible structures
    ads = search_results.get("ads", [])
    organic = search_results.get("organic_results", [])
    local_services = search_results.get("local_ads", [])

    # Handle local_results which can be dict or list
    local_pack = search_results.get("local_results", {})
    if isinstance(local_pack, dict):
        local_pack = local_pack.get("places", [])
    elif not isinstance(local_pack, list):
        local_pack = []

    # Filter directories from organic count
    real_organic = [
        r for r in organic
        if not _is_directory(r.get("displayed_link", "") or r.get("link", ""))
    ]

    ads_count = len(ads) if isinstance(ads, list) else 0
    organic_count = len(real_organic)
    maps_count = len(local_pack) if isinstance(local_pack, list) else 0
    local_services_count = len(local_services) if isinstance(local_services, list) else 0

    # Detect franchises in results
    all_text = str(search_results).lower()
    franchises_found = []

    for pattern, name in FRANCHISE_PATTERNS.items():
        if pattern in all_text and name not in franchises_found:
            franchises_found.append(name)

    has_major_franchise = len(franchises_found) > 0

    # Calculate score (start at 100, subtract for competition signals)
    score = 100

    # === Ads penalty (strongest signal of commercial competition) ===
    if ads_count >= 4:
        score -= 30
        notes.append(f"Heavy ads ({ads_count})")
    elif ads_count >= 2:
        score -= 20
        notes.append(f"Moderate ads ({ads_count})")
    elif ads_count == 1:
        score -= 10
        notes.append("Some ad competition")
    else:
        notes.append("No ads")

    # === Organic penalty ===
    if organic_count >= 10:
        score -= 20
        notes.append("Full organic results")
    elif organic_count >= 7:
        score -= 15
    elif organic_count >= 4:
        score -= 10
    elif organic_count < 3:
        score += 5  # Bonus for thin organic results
        notes.append("Thin organic - ranking opportunity")

    # === Maps penalty ===
    if maps_count >= 20:
        score -= 15
        notes.append("Crowded maps")
    elif maps_count >= 10:
        score -= 10
    elif maps_count < 5:
        score += 5  # Bonus for sparse maps
        notes.append("Few maps listings")

    # === Local services (Google Guaranteed) penalty ===
    if local_services_count >= 5:
        score -= 15
        notes.append("Heavy Google Guaranteed")
    elif local_services_count >= 2:
        score -= 10
    elif local_services_count >= 1:
        score -= 5

    # === Franchise penalty (big players = hard to compete) ===
    if len(franchises_found) >= 3:
        score -= 25
        notes.append(f"Multiple franchises: {', '.join(franchises_found[:2])}")
    elif len(franchises_found) >= 1:
        score -= 15
        notes.append(f"Franchise: {franchises_found[0]}")

    # Clamp score to 0-100
    score = max(0, min(100, score))

    # Determine saturation level
    if score >= 76:
        saturation = "low"
    elif score >= 51:
        saturation = "medium"
    elif score >= 26:
        saturation = "high"
    else:
        saturation = "saturated"

    return CompetitionAnalysis(
        score=score,
        saturation=saturation,
        ads_count=ads_count,
        organic_count=organic_count,
        maps_count=maps_count,
        franchises_found=franchises_found,
        has_major_franchise=has_major_franchise,
        notes=notes,
    )


def _is_directory(url: str) -> bool:
    """Check if URL is a directory/aggregator site."""
    url_lower = url.lower()
    return any(d in url_lower for d in DIRECTORY_DOMAINS)


def get_competition_notes(analysis: CompetitionAnalysis) -> str:
    """Generate human-readable competition notes."""
    parts = []

    # Saturation summary
    saturation_text = {
        "low": "Low competition market - excellent opportunity",
        "medium": "Moderate competition - good potential",
        "high": "Competitive market - need strong differentiation",
        "saturated": "Highly saturated market - difficult to compete",
    }
    parts.append(saturation_text[analysis.saturation])

    # Key notes (top 3)
    if analysis.notes:
        parts.extend(analysis.notes[:3])

    return "; ".join(parts)


def get_default_competition() -> CompetitionAnalysis:
    """Return default medium competition when no search context available."""
    return CompetitionAnalysis(
        score=50,
        saturation="medium",
        ads_count=0,
        organic_count=0,
        maps_count=0,
        franchises_found=[],
        has_major_franchise=False,
        notes=["No search context - using default"],
    )
