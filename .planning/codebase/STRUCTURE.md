# Codebase Structure

**Analysis Date:** 2026-02-01

## Directory Layout

```
prospect-command-center/
├── prospect/              # Main Python package
│   ├── scraper/          # Search execution (SerpAPI, orchestration)
│   ├── enrichment/       # Website analysis (crawler, contacts, tech)
│   ├── scoring/          # Prospect prioritization (fit, opportunity)
│   ├── sheets/           # Google Sheets integration
│   └── web/              # FastAPI application
│       ├── api/v1/       # REST API endpoints
│       ├── ws/           # WebSocket handlers
│       ├── frontend/     # SPA assets (JS, HTML, PWA)
│       └── templates/    # Jinja2 templates
├── tests/                # Test files
├── docker/               # Docker configuration
├── .planning/            # Project planning documents
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Build config, tool settings
├── Makefile              # Dev automation
└── Procfile              # Railway deployment
```

## Directory Purposes

**prospect/**
- Purpose: Main application package
- Contains: Core modules (api.py, cli.py, config.py, models.py)
- Key files: `api.py` (public API), `cli.py` (CLI entry), `models.py` (data models)
- Subdirectories: scraper/, enrichment/, scoring/, sheets/, web/

**prospect/scraper/**
- Purpose: Search execution and result parsing
- Contains: SerpAPI client, search orchestration, location handling
- Key files: `serpapi.py` (API client), `orchestrator.py` (multi-channel), `locations.py`
- Subdirectories: None

**prospect/enrichment/**
- Purpose: Website analysis and data extraction
- Contains: Async crawler, contact extraction, technology detection
- Key files: `crawler.py` (httpx crawler), `contacts.py` (email/phone), `technology.py` (CMS/tracking)
- Subdirectories: None

**prospect/scoring/**
- Purpose: Prospect prioritization algorithms
- Contains: Fit scoring, opportunity scoring, note generation
- Key files: `fit.py`, `opportunity.py`, `notes.py`
- Subdirectories: None

**prospect/sheets/**
- Purpose: Google Sheets export integration
- Contains: Sheets API client, data formatting, OAuth auth
- Key files: `client.py`, `formatter.py`, `auth.py`
- Subdirectories: None

**prospect/web/**
- Purpose: FastAPI web application
- Contains: App factory, auth, database, routes, tasks
- Key files: `app.py` (factory), `database.py` (ORM), `auth.py` (JWT), `tasks.py` (background)
- Subdirectories: api/v1/, ws/, frontend/, templates/

**prospect/web/api/v1/**
- Purpose: REST API v1 endpoints
- Contains: Route handlers for all API resources
- Key files: `router.py` (orchestrator), `auth.py`, `search.py`, `billing.py`, `usage.py`
- Subdirectories: None

**prospect/web/frontend/**
- Purpose: Progressive Web App SPA
- Contains: Vanilla JS app, HTML shell, service worker
- Key files: `app.js` (logic), `index.html` (shell), `sw.js` (PWA), `manifest.json`
- Subdirectories: None

**tests/**
- Purpose: Test files (pytest)
- Contains: Unit and integration tests
- Key files: `test_enrichment.py`, `test_web.py`, `test_search_depth.py`, `test_data_accuracy.py`
- Subdirectories: None

## Key File Locations

**Entry Points:**
- `prospect/web/app.py` - FastAPI application factory
- `prospect/cli.py` - CLI entry point (Click)
- `prospect/api.py` - Programmatic API for library usage

**Configuration:**
- `pyproject.toml` - Build config, dependencies, Black/Ruff/pytest settings
- `.env.example` - Environment variable template
- `config.example.yaml` - YAML config for scoring weights
- `prospect/config.py` - Settings dataclass and config loading

**Core Logic:**
- `prospect/scraper/serpapi.py` - SerpAPI client
- `prospect/enrichment/crawler.py` - Website enrichment
- `prospect/scoring/fit.py` - Fit score calculation
- `prospect/scoring/opportunity.py` - Opportunity score calculation
- `prospect/dedup.py` - Deduplication logic

**Database:**
- `prospect/web/database.py` - SQLAlchemy models (User, Search, Prospect, Campaign, etc.)

**Testing:**
- `tests/test_enrichment.py` - Email/contact extraction tests
- `tests/test_web.py` - FastAPI endpoint tests
- `tests/test_data_accuracy.py` - Domain normalization tests

**Documentation:**
- `README.md` - User-facing documentation
- `CONTRIBUTING.md` - Developer guide and code style

## Naming Conventions

**Files:**
- snake_case.py for all Python modules (`serpapi.py`, `crawler.py`, `billing.py`)
- test_*.py for test files (`test_enrichment.py`, `test_web.py`)
- Lowercase with hyphens for config files (`docker-compose.yml`)

**Directories:**
- snake_case for packages (`enrichment/`, `scoring/`, `scraper/`)
- Plural for collections (`tests/`, `templates/`)

**Special Patterns:**
- `__init__.py` for package initialization
- `router.py` for API route aggregation
- `models.py` for data models (both Pydantic and SQLAlchemy)

## Where to Add New Code

**New API Endpoint:**
- Primary code: `prospect/web/api/v1/{resource}.py`
- Register in: `prospect/web/api/v1/router.py`
- Tests: `tests/test_{resource}.py`

**New Search/Enrichment Feature:**
- Search logic: `prospect/scraper/{feature}.py`
- Enrichment: `prospect/enrichment/{feature}.py`
- Tests: `tests/test_{feature}.py`

**New Scoring Algorithm:**
- Implementation: `prospect/scoring/{algorithm}.py`
- Integration: Update `prospect/api.py` pipeline
- Tests: `tests/test_scoring.py`

**New Export Format:**
- Implementation: `prospect/export.py` or `prospect/sheets/`
- Tests: `tests/test_export.py`

**Utilities:**
- Shared helpers: `prospect/validation.py` or `prospect/constants.py`
- Config: `prospect/config.py`

## Special Directories

**prospect/web/frontend/**
- Purpose: Static SPA assets served by FastAPI
- Source: Hand-written vanilla JS, Tailwind via CDN
- Committed: Yes (no build step required)

**docker/**
- Purpose: Docker configuration files
- Source: `Dockerfile`, compose files for dev/prod/beta
- Committed: Yes

**.planning/**
- Purpose: GSD planning documents
- Source: Generated by `/gsd:*` commands
- Committed: Yes (project documentation)

---

*Structure analysis: 2026-02-01*
*Update when directory structure changes*
