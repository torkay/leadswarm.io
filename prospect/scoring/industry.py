"""
Industry Value Classifier

Classifies businesses into value tiers based on:
- Market commoditisation (everyone does it = low value)
- Typical client margins
- Complexity of marketing needs
- Likelihood to pay premium rates

Categories:
- commoditised: 0.4-0.6x (plumbers, cleaners - race to bottom)
- standard: 0.8-1.0x (accountants, dentists - normal competition)
- niche: 1.2-1.4x (buyer's agents, architects - specialised)
- specialist: 1.4-1.6x (aviation, marine, medical equipment - very rare)
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class IndustryClassification:
    """Industry classification result."""
    category: str  # commoditised, standard, niche, specialist
    multiplier: float  # 0.4 - 1.6
    confidence: float  # 0-1
    matched_keywords: List[str]
    notes: str


# Pattern format: (keywords, category, multiplier, notes)
INDUSTRY_PATTERNS: List[Tuple[List[str], str, float, str]] = [
    # === COMMODITISED (0.4-0.6) ===
    # High volume, low margin, race to bottom
    (["lawn mow", "mowing", "grass cut"], "commoditised", 0.4, "Highly commoditised, price war market"),
    (["cleaner", "cleaning service", "house clean", "office clean", "domestic clean"], "commoditised", 0.5, "High competition, low margins"),
    (["rubbish removal", "junk removal", "skip bin", "waste removal"], "commoditised", 0.5, "Price-driven commodity"),
    (["plumber", "plumbing", "blocked drain", "gas fitter", "hot water"], "commoditised", 0.6, "Franchise-heavy market"),
    (["electrician", "electrical", "sparky"], "commoditised", 0.6, "Commoditised trade"),
    (["painter", "painting service", "house paint"], "commoditised", 0.55, "Low barrier to entry"),
    (["handyman", "odd jobs", "home repair"], "commoditised", 0.5, "Gig economy competition"),
    (["removalist", "moving service", "furniture remov"], "commoditised", 0.55, "Seasonal, price-sensitive"),
    (["pest control", "termite", "exterminator"], "commoditised", 0.6, "Some franchise competition"),
    (["carpet clean", "upholstery clean"], "commoditised", 0.5, "Low differentiation"),
    (["pressure wash", "pressure clean"], "commoditised", 0.5, "Easy entry market"),
    (["gutter clean", "roof clean"], "commoditised", 0.55, "Seasonal commodity"),
    (["locksmith"], "commoditised", 0.55, "Emergency service commodity"),
    (["towing", "tow truck"], "commoditised", 0.55, "Emergency service"),

    # === STANDARD (0.8-1.0) ===
    # Normal service businesses, moderate competition
    (["accountant", "accounting", "bookkeeper", "tax agent", "bas agent"], "standard", 0.9, "Professional service"),
    (["lawyer", "solicitor", "legal service"], "standard", 1.0, "Regulated profession"),
    (["dentist", "dental"], "standard", 0.95, "Healthcare, location-dependent"),
    (["physio", "physiotherap", "chiropractor", "osteopath"], "standard", 0.9, "Allied health"),
    (["mechanic", "auto repair", "car service"], "standard", 0.85, "Established trade"),
    (["hairdresser", "hair salon", "barber", "beauty salon"], "standard", 0.85, "Personal service"),
    (["real estate agent", "property manager"], "standard", 0.9, "Franchise presence"),
    (["mortgage broker", "finance broker"], "standard", 0.95, "Financial service"),
    (["photographer", "videographer"], "standard", 0.85, "Creative, portfolio-driven"),
    (["web design", "web develop", "website design"], "standard", 0.9, "Technical service"),
    (["personal trainer", "fitness coach"], "standard", 0.8, "Personal service"),
    (["florist", "flower shop"], "standard", 0.85, "Retail/service hybrid"),
    (["vet", "veterinar"], "standard", 0.9, "Healthcare"),
    (["optometrist", "optical"], "standard", 0.9, "Healthcare retail"),
    (["psycholog", "counsell", "therapist"], "standard", 0.95, "Mental health professional"),
    (["massage", "remedial massage"], "standard", 0.85, "Wellness service"),
    (["podiatr", "foot clinic"], "standard", 0.9, "Allied health"),
    (["baker", "bakery", "cake shop"], "standard", 0.85, "Food retail"),
    (["restaurant", "cafe", "coffee shop"], "standard", 0.8, "Hospitality"),
    (["caterer", "catering"], "standard", 0.85, "Event service"),

    # === NICHE (1.2-1.4) ===
    # Specialised services, less competition
    (["buyer's agent", "buyers agent", "buyer agent", "buyers advocate"], "niche", 1.4, "High-value property niche"),
    (["architect", "architectural"], "niche", 1.3, "Professional design"),
    (["interior design"], "niche", 1.25, "Design specialist"),
    (["landscape architect", "landscape design", "garden design"], "niche", 1.25, "Outdoor design specialist"),
    (["heritage", "restoration", "conservation"], "niche", 1.4, "Heritage specialist"),
    (["migration agent", "immigration", "visa agent"], "niche", 1.35, "Specialist legal"),
    (["financial planner", "wealth advis", "financial advis"], "niche", 1.3, "High-value professional"),
    (["building certif", "building inspect", "pre-purchase inspect"], "niche", 1.2, "Specialist inspection"),
    (["quantity survey", "cost estimat"], "niche", 1.25, "Construction specialist"),
    (["town planner", "urban planner", "planning consult"], "niche", 1.3, "Development specialist"),
    (["acoustic", "noise consult", "sound engineer"], "niche", 1.35, "Technical specialist"),
    (["survey", "land survey", "cadastral"], "niche", 1.25, "Licensed specialist"),
    (["arborist", "tree surgeon"], "niche", 1.2, "Specialist trade"),
    (["pool build", "swimming pool construct"], "niche", 1.2, "Specialist construction"),
    (["commercial fitout", "office fitout", "shopfitt"], "niche", 1.3, "Commercial specialist"),
    (["strata manag", "body corporate"], "niche", 1.35, "Property management niche"),
    (["customs broker", "freight forward"], "niche", 1.3, "Import/export specialist"),
    (["ip lawyer", "patent attorney", "trademark"], "niche", 1.4, "Specialist legal"),
    (["family law", "divorce lawyer"], "niche", 1.25, "Specialist legal"),
    (["conveyancer", "conveyancing"], "niche", 1.2, "Property legal specialist"),
    (["executive coach", "business coach", "leadership coach"], "niche", 1.35, "High-value consulting"),
    (["hr consult", "recruitment agency"], "niche", 1.25, "Business service"),

    # === SPECIALIST (1.4-1.6) ===
    # Highly specialised, very low competition
    (["aviation", "aircraft", "helicopter", "pilot training"], "specialist", 1.6, "Highly specialised"),
    (["marine survey", "boat survey", "vessel inspect"], "specialist", 1.5, "Marine specialist"),
    (["marine engineer", "boat mechanic"], "specialist", 1.45, "Marine trade"),
    (["medical equipment", "healthcare equipment"], "specialist", 1.5, "Medical industry"),
    (["veterinary specialist", "animal surgeon", "equine vet"], "specialist", 1.45, "Specialist vet"),
    (["mining consult", "resources consult", "geolog"], "specialist", 1.5, "Resources sector"),
    (["environmental consult", "ecology", "contamination"], "specialist", 1.4, "Environmental specialist"),
    (["elevator", "lift service", "escalator"], "specialist", 1.45, "Vertical transport"),
    (["fire protection", "fire engineer", "sprinkler system"], "specialist", 1.4, "Fire safety specialist"),
    (["data centre", "server room"], "specialist", 1.5, "IT infrastructure"),
    (["ev charger", "electric vehicle charg"], "specialist", 1.4, "Emerging specialist"),
    (["solar install", "solar panel"], "niche", 1.2, "Renewable energy (becoming commoditised)"),
    (["cybersecurity", "penetration test", "security audit"], "specialist", 1.5, "IT security"),
    (["forensic account", "fraud investigat"], "specialist", 1.5, "Specialist accounting"),
    (["medical special", "surgeon", "cardiolog", "oncolog"], "specialist", 1.5, "Medical specialist"),
    (["aerospace", "defence contractor"], "specialist", 1.6, "High-security sector"),
    (["nuclear", "radiation"], "specialist", 1.6, "Regulated specialist"),
    (["subsea", "offshore", "diving contractor"], "specialist", 1.5, "Marine/oil & gas"),
]


def classify_industry(
    business_type: str,
    business_name: Optional[str] = None,
) -> IndustryClassification:
    """
    Classify business into value category.

    Args:
        business_type: Search query or business type (e.g., "plumber", "buyer's agent")
        business_name: Optional business name for additional context

    Returns:
        IndustryClassification with category and multiplier
    """
    search_text = business_type.lower()
    if business_name:
        search_text += " " + business_name.lower()

    best_match = None
    best_match_score = 0
    matched_keywords = []

    for keywords, category, multiplier, notes in INDUSTRY_PATTERNS:
        # Count keyword matches
        matches = [kw for kw in keywords if kw.lower() in search_text]
        match_score = len(matches)

        # Prefer longer keyword matches (more specific)
        if matches:
            match_score += max(len(m) for m in matches) / 100

        if match_score > best_match_score:
            best_match_score = match_score
            best_match = (category, multiplier, notes)
            matched_keywords = matches

    if best_match and best_match_score > 0:
        category, multiplier, notes = best_match
        confidence = min(1.0, best_match_score * 0.4)

        return IndustryClassification(
            category=category,
            multiplier=multiplier,
            confidence=confidence,
            matched_keywords=matched_keywords,
            notes=notes,
        )

    # Default: standard category
    return IndustryClassification(
        category="standard",
        multiplier=1.0,
        confidence=0.2,
        matched_keywords=[],
        notes="Unclassified - using default",
    )


def get_industry_multiplier(business_type: str) -> float:
    """Simple helper to get just the multiplier."""
    return classify_industry(business_type).multiplier


def get_industry_category(business_type: str) -> str:
    """Simple helper to get just the category."""
    return classify_industry(business_type).category


def get_industry_notes(classification: IndustryClassification) -> str:
    """Generate human-readable industry notes."""
    category_text = {
        "commoditised": "Commoditised market",
        "standard": "Standard service market",
        "niche": "Niche specialist market",
        "specialist": "Highly specialised market",
    }

    return f"{category_text[classification.category]} ({classification.multiplier}x); {classification.notes}"
