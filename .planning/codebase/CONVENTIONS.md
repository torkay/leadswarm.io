# Coding Conventions

**Analysis Date:** 2026-02-01

## Naming Patterns

**Files:**
- snake_case for all Python files (`serpapi.py`, `crawler.py`, `billing.py`)
- test_*.py for test files (`test_enrichment.py`, `test_web.py`)
- UPPERCASE.md for important docs (`README.md`, `CONTRIBUTING.md`)

**Functions:**
- snake_case for all functions (`calculate_fit_score`, `extract_emails`, `normalize_domain`)
- Action verbs at start (`search_prospects`, `enrich_prospect`, `validate_phone`)
- Leading underscore for private functions (`_extract_social_links`)
- Async functions use same naming (no special prefix)

**Variables:**
- snake_case for all variables (`business_type`, `fit_score`, `opportunity_score`)
- UPPER_SNAKE_CASE for constants (`AU_AREA_CODES`, `AU_STATES`, `DIRECTORY_DOMAINS`)
- Boolean variables: `is_*` or `has_*` prefix (`is_spam_email`, `has_google_analytics`)

**Types:**
- PascalCase for classes (`Prospect`, `WebsiteSignals`, `SerpAPIClient`)
- PascalCase for dataclasses (`ProspectResult`, `CrawlResult`, `SerpResults`)
- PascalCase + Error suffix for exceptions (`SerpAPIError`, `AuthenticationError`)

## Code Style

**Formatting:**
- Black formatter with 100 character line length (`pyproject.toml`)
- Double quotes for strings (Black default)
- 4-space indentation (Python standard)
- No semicolons

**Linting:**
- Ruff linter with rules: E, F, W, I, N, UP
- Line length: 100 (ignores E501)
- Target versions: py310, py311, py312
- Run: `make lint` or `ruff check prospect/ tests/`

## Import Organization

**Order:**
1. Standard library (asyncio, dataclasses, typing, logging)
2. Third-party packages (fastapi, sqlalchemy, stripe, httpx)
3. Local imports (relative: `.config`, `.scraper`, `.models`)

**Grouping:**
- Blank line between groups
- Alphabetical within each group
- Type imports with regular imports (no separate section)

**Path Aliases:**
- Relative imports for internal modules (`.config`, `..models`)
- No @ aliases configured

## Error Handling

**Patterns:**
- Raise exceptions in services, catch at API boundaries
- Custom exceptions extend base Exception class
- Try/catch with specific exception types

**Error Types:**
- `SerpAPIError` for search API failures
- `AuthenticationError` for auth issues
- HTTPException with status codes for API errors

**Logging:**
- `logger.exception()` for full stack traces
- `logger.error()` for error messages with context
- `logger.debug()` for detailed tracing

## Logging

**Framework:**
- Standard `logging` module
- `logger = logging.getLogger(__name__)` at module level

**Patterns:**
- Structured logging with context: `logger.debug("Failed to enrich %s: %s", prospect.name, e)`
- Levels: debug, info, warning, error
- No console.log equivalents in production code

## Comments

**When to Comment:**
- Explain why, not what
- Document business logic and edge cases
- Mark important notes with "IMPORTANT:" prefix

**Docstrings:**
- Triple-quoted docstrings for modules, classes, functions
- Format: Description, Args, Returns, Examples sections
- Required for public API functions
- Example from `prospect/api.py`:
```python
def search_prospects(
    business_type: str,
    location: str,
    ...
) -> ProspectResult:
    """Search for business prospects and enrich with website data.

    Args:
        business_type: Type of business to search for
        location: Geographic location to search in
        ...

    Returns:
        ProspectResult with list of prospects and metadata
    """
```

**TODO Comments:**
- Format: `# TODO: description`
- No username required (use git blame)

## Function Design

**Size:**
- Keep functions focused and under 50 lines when practical
- Extract helpers for complex logic

**Parameters:**
- Type hints for all parameters
- Use Optional for nullable params: `location: Optional[str] = None`
- Use dataclasses for complex parameter objects

**Return Values:**
- Type hints for return values
- Return early for guard clauses
- Use dataclasses for complex return types (`ProspectResult`, `CrawlResult`)

## Module Design

**Exports:**
- Named exports preferred
- No `__all__` declarations (implicit exports)
- Public API in `prospect/api.py`

**Async Patterns:**
- Async context managers for resources: `async with WebsiteCrawler() as crawler:`
- `asyncio` for concurrent operations
- `httpx` for async HTTP

## Type Hints

**Usage:**
- Comprehensive type hints throughout
- Modern syntax: `list[str]` instead of `List[str]` for Python 3.10+
- Use `Optional`, `Union`, `dict`, `list` from typing module
- Dataclass fields with explicit types

**Examples:**
```python
def search_prospects(
    business_type: str,
    location: str,
    num_results: int = 10,
    skip_enrichment: bool = False,
) -> ProspectResult:
```

## Localization

**Spelling:**
- British/Australian English in UI copy (`prospect/constants.py`)
- Examples: "colour", "organisation", "analyse"
- Consistent throughout user-facing text

---

*Convention analysis: 2026-02-01*
*Update when patterns change*
