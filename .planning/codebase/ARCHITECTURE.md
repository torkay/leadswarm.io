# Architecture

**Analysis Date:** 2026-02-01

## Pattern Overview

**Overall:** Layered + Service-Oriented Hybrid (Full-Stack Python Application)

**Key Characteristics:**
- Dual entry points (CLI + Web Server)
- Multi-stage ETL pipeline (Search → Enrich → Score → Export)
- Progressive Web App frontend (Vanilla JS SPA)
- Multi-tenant with JWT auth and Stripe billing
- Real-time updates via WebSocket

## Layers

**Presentation Layer:**
- Purpose: User interface and HTTP/WebSocket endpoints
- Contains: FastAPI routes, Jinja2 templates, SPA frontend
- Location: `prospect/web/api/v1/*.py`, `prospect/web/frontend/`
- Depends on: Service layer
- Used by: End users, API consumers

**API Layer:**
- Purpose: REST API endpoints with authentication
- Contains: Route handlers, request validation, response formatting
- Location: `prospect/web/api/v1/router.py` (orchestrator)
- Depends on: Service layer, auth utilities
- Used by: Frontend SPA, external API consumers

**Service Layer:**
- Purpose: Core business logic for search, enrichment, scoring
- Contains: Search orchestration, website crawling, scoring algorithms
- Location: `prospect/scraper/`, `prospect/enrichment/`, `prospect/scoring/`
- Depends on: Data layer, external APIs (SerpAPI, Stripe)
- Used by: API layer, CLI

**Data Layer:**
- Purpose: Database models and persistence
- Contains: SQLAlchemy ORM models, database engine
- Location: `prospect/web/database.py`
- Depends on: SQLite/PostgreSQL
- Used by: Service layer, API layer

**Utility Layer:**
- Purpose: Shared helpers and configuration
- Contains: Validation, export, constants, config loading
- Location: `prospect/config.py`, `prospect/validation.py`, `prospect/constants.py`
- Depends on: Python stdlib
- Used by: All layers

## Data Flow

**Web UI Search Request:**

1. User submits search form in frontend (`prospect/web/frontend/app.js`)
2. POST `/api/v1/search/start` with auth token (`prospect/web/api/v1/search.py`)
3. Create Job, check usage limits, start background task (`prospect/web/tasks.py`)
4. `SearchOrchestrator.execute()` runs SerpAPI search (`prospect/scraper/orchestrator.py`)
5. Deduplicate results (`prospect/dedup.py`)
6. Enrich prospects async via `WebsiteCrawler` (`prospect/enrichment/crawler.py`)
7. Calculate fit and opportunity scores (`prospect/scoring/fit.py`, `prospect/scoring/opportunity.py`)
8. Store results in database, update job status
9. WebSocket pushes progress to frontend (`prospect/web/ws/jobs.py`)
10. Display results in sortable table

**CLI Search Request:**

1. User runs `prospect search "plumber" "Sydney"` (`prospect/cli.py`)
2. `search_prospects()` API function called (`prospect/api.py`)
3. SerpAPI search → dedup → enrich → score pipeline
4. Format and display results to terminal

**State Management:**
- File-based: SQLite database for persistent storage
- In-memory: `job_manager` singleton for active job tracking (`prospect/web/state.py`)
- Each request is stateless (JWT auth, no server sessions)

## Key Abstractions

**SerpAPIClient:**
- Purpose: Search execution with location normalization, retry logic
- Examples: `prospect/scraper/serpapi.py`
- Pattern: Client wrapper with tenacity retry decorator

**WebsiteCrawler:**
- Purpose: Async website analysis for enrichment
- Examples: `prospect/enrichment/crawler.py`
- Pattern: Async context manager with httpx

**Scoring System:**
- Purpose: Prospect prioritization via fit + opportunity scores
- Examples: `prospect/scoring/fit.py`, `prospect/scoring/opportunity.py`
- Pattern: Modular component weights, YAML-configurable

**JobManager:**
- Purpose: Track background search jobs
- Examples: `prospect/web/state.py`
- Pattern: Singleton with WebSocket broadcast

## Entry Points

**Web Server:**
- Location: `prospect/web/app.py` - `create_app()` factory
- Triggers: HTTP requests, uvicorn startup
- Responsibilities: Initialize FastAPI, mount routes, serve frontend

**CLI:**
- Location: `prospect/cli.py` - Click CLI
- Triggers: `prospect <command>` terminal invocation
- Responsibilities: Parse args, execute commands (search, batch, web)

**Programmatic API:**
- Location: `prospect/api.py` - `search_prospects()`
- Triggers: Library import
- Responsibilities: Provide clean API for library users

## Error Handling

**Strategy:** Raise exceptions in services, catch at API boundaries

**Patterns:**
- Custom exceptions: `SerpAPIError`, `AuthenticationError`
- HTTP exceptions in routes with appropriate status codes
- Logger with context: `logger.exception()` for stack traces
- Graceful degradation: Enrichment failures don't block search results

## Cross-Cutting Concerns

**Logging:**
- Standard `logging` module with `logging.getLogger(__name__)`
- Structured logging with context objects

**Validation:**
- Pydantic models for API request/response validation
- Custom validators in `prospect/validation.py` (email, phone, domain)

**Authentication:**
- JWT tokens with 7-day expiration (`prospect/web/auth.py`)
- `get_current_user()` dependency for protected routes
- Password hashing via bcrypt

**Usage Tracking:**
- Per-tier limits (scout/hunter/command)
- Monthly usage records in database
- Enforcement via `require_search_limit()` dependency

---

*Architecture analysis: 2026-02-01*
*Update when major patterns change*
