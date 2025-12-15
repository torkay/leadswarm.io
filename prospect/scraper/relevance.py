"""Business relevance filtering to prevent false positives.

Filters out irrelevant businesses that appear in search results due to
mixed searches or overly broad matching.
"""

from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Aggregator domains to always filter (not real businesses)
AGGREGATORS = {
    "yellowpages", "truelocal", "hotfrog", "yelp", "airtasker",
    "hipages", "oneflare", "serviceseeking", "visitorsguide",
    "localsearch", "startlocal", "dlook", "whitepages",
    "infobel", "cylex", "aussieweb", "findlocal",
}

# Irrelevant business types (filter unless specifically searching for them)
IRRELEVANT_TYPES = {
    "internet cafe", "cyber cafe", "gaming", "esports", "lan cafe",
    "restaurant", "cafe", "coffee", "bakery", "takeaway",
    "hotel", "motel", "hostel", "gym", "fitness", "yoga",
    "hairdresser", "barber", "beauty salon", "nail salon",
    "supermarket", "grocery", "convenience store",
    "fast food", "pizza", "burger", "kebab",
}

# Business type synonyms for matching
SYNONYMS = {
    "buyer's agent": {"buyer", "buyers", "advocate", "advocacy", "property buyer", "buyer agent"},
    "buyers agent": {"buyer", "buyers", "advocate", "advocacy", "property buyer", "buyer agent"},
    "plumber": {"plumber", "plumbing", "drain", "gas fitter", "gasfitter"},
    "electrician": {"electrician", "electrical", "sparky", "electric"},
    "accountant": {"accountant", "accounting", "bookkeeper", "tax", "cpa"},
    "real estate": {"real estate", "realestate", "property", "realtor"},
    "lawyer": {"lawyer", "solicitor", "attorney", "legal", "law firm"},
    "dentist": {"dentist", "dental", "orthodontist"},
    "doctor": {"doctor", "medical", "clinic", "gp", "physician"},
    "mechanic": {"mechanic", "automotive", "auto repair", "car service"},
    "builder": {"builder", "construction", "contractor", "building"},
    "painter": {"painter", "painting", "decorator"},
    "landscaper": {"landscaper", "landscaping", "garden", "lawn"},
    "cleaner": {"cleaner", "cleaning", "maid", "janitor"},
    "removalist": {"removalist", "removal", "moving", "mover"},
    "photographer": {"photographer", "photography", "photo studio"},
    "web developer": {"web developer", "web design", "website", "developer"},
    "marketing": {"marketing", "digital marketing", "seo", "advertising"},
}


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    return text.lower().strip()


def get_synonyms_for_query(query: str) -> set:
    """Get all synonyms for a search query."""
    query_lower = normalize_text(query)

    for base_term, syns in SYNONYMS.items():
        # Check if query matches base term or any synonym
        if base_term in query_lower or any(s in query_lower for s in syns):
            return syns | {base_term}

    # No synonyms found, use the query terms as-is
    return {query_lower}


def is_aggregator(domain: Optional[str]) -> bool:
    """Check if domain is an aggregator site."""
    if not domain:
        return False

    domain_lower = normalize_text(domain)
    return any(agg in domain_lower for agg in AGGREGATORS)


def is_irrelevant_type(name: str, business_type: Optional[str], query: str) -> bool:
    """Check if business appears to be an irrelevant type."""
    query_lower = normalize_text(query)
    name_lower = normalize_text(name)
    type_lower = normalize_text(business_type or "")

    for irr_type in IRRELEVANT_TYPES:
        # Skip if searching for this type
        if irr_type in query_lower:
            continue

        # Filter if name or type contains irrelevant term
        if irr_type in name_lower or irr_type in type_lower:
            return True

    return False


def matches_query_type(name: str, domain: Optional[str], query: str) -> bool:
    """Check if business name/domain matches the query type."""
    name_lower = normalize_text(name)
    domain_lower = normalize_text(domain or "")

    synonyms = get_synonyms_for_query(query)

    # Check if any synonym appears in name or domain
    for syn in synonyms:
        if syn in name_lower or syn in domain_lower:
            return True

    return False


def is_relevant(
    name: str,
    domain: Optional[str],
    business_type: Optional[str],
    search_query: str,
    strict: bool = False,
) -> Tuple[bool, str]:
    """
    Check if a business is relevant to the search query.

    Args:
        name: Business name
        domain: Business domain/website
        business_type: Business type/category from search results
        search_query: The original search query
        strict: If True, require positive match to query type

    Returns:
        Tuple of (is_relevant, reason)
    """
    # Check aggregators
    if is_aggregator(domain):
        return False, f"Aggregator domain"

    # Check irrelevant types
    if is_irrelevant_type(name, business_type, search_query):
        return False, "Irrelevant business type"

    # In strict mode, require positive match
    if strict:
        if not matches_query_type(name, domain, search_query):
            return False, "No match for query type"

    return True, "Relevant"


def filter_prospects(
    prospects: List[dict],
    search_query: str,
    strict: bool = False,
) -> Tuple[List[dict], List[dict]]:
    """
    Filter out irrelevant prospects.

    Args:
        prospects: List of prospect dictionaries
        search_query: The original search query
        strict: If True, require positive match to query type

    Returns:
        Tuple of (filtered_prospects, removed_prospects)
    """
    filtered = []
    removed = []

    for p in prospects:
        name = p.get("name", "")
        domain = p.get("domain", "")
        business_type = p.get("type", "") or p.get("business_type", "")

        relevant, reason = is_relevant(
            name=name,
            domain=domain,
            business_type=business_type,
            search_query=search_query,
            strict=strict,
        )

        if relevant:
            filtered.append(p)
        else:
            logger.debug(f"Filtered: {name} - {reason}")
            p["_filtered_reason"] = reason
            removed.append(p)

    if removed:
        logger.info(f"Filtered {len(removed)} irrelevant prospects from {len(prospects)} total")

    return filtered, removed


def filter_prospect_objects(
    prospects: List,
    search_query: str,
    strict: bool = False,
) -> List:
    """
    Filter prospect objects (not dictionaries).

    Args:
        prospects: List of Prospect objects with name, domain attributes
        search_query: The original search query
        strict: If True, require positive match to query type

    Returns:
        Filtered list of prospects
    """
    filtered = []

    for p in prospects:
        name = getattr(p, "name", "") or ""
        domain = getattr(p, "domain", "") or ""
        business_type = getattr(p, "business_type", "") or getattr(p, "type", "") or ""

        relevant, reason = is_relevant(
            name=name,
            domain=domain,
            business_type=business_type,
            search_query=search_query,
            strict=strict,
        )

        if relevant:
            filtered.append(p)
        else:
            logger.debug(f"Filtered prospect: {name} - {reason}")

    return filtered
