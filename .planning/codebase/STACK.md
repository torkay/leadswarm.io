# Technology Stack

**Analysis Date:** 2026-02-01

## Languages

**Primary:**
- Python 3.11 - All backend application code (`/.python-version`, `pyproject.toml`)

**Secondary:**
- JavaScript - Vanilla JS for frontend UI (`prospect/web/frontend/app.js`)
- HTML/CSS - Tailwind CSS via CDN (`prospect/web/frontend/index.html`)

## Runtime

**Environment:**
- Python 3.11 (specified in `/.python-version`)
- Supports 3.10, 3.11, 3.12 (per `pyproject.toml` Ruff targets)

**Package Manager:**
- pip
- Lockfile: `requirements.txt` (27 packages, no lockfile)

## Frameworks

**Core:**
- FastAPI 0.104.0+ - Web framework (`prospect/web/app.py`)
- Uvicorn 0.24.0+ - ASGI server (`Procfile`, `docker/Dockerfile`)
- SQLAlchemy 2.0.0+ - ORM (`prospect/web/database.py`)

**Testing:**
- pytest - Test runner (`pyproject.toml`)
- pytest-asyncio - Async test support
- pytest-cov - Coverage reporting

**Build/Dev:**
- Docker - Containerization (`docker/Dockerfile`)
- Makefile - Build automation (`Makefile`)
- Black - Code formatter (100 char line length)
- Ruff - Linter

## Key Dependencies

**Critical:**
- stripe - Payment processing and subscription billing (`prospect/web/api/v1/billing.py`)
- python-jose[cryptography] 3.3.0+ - JWT token handling (`prospect/web/auth.py`)
- passlib[bcrypt] 1.7.4+ - Password hashing (`prospect/web/auth.py`)
- gspread 5.12.0+ - Google Sheets export (`prospect/sheets/client.py`)
- httpx 0.25.0+ - Async HTTP client for enrichment (`prospect/scraper/serpapi.py`)

**Infrastructure:**
- aiosqlite 0.19.0+ - Async SQLite driver
- playwright 1.40.0+ - Browser automation for scraping
- playwright-stealth 1.0.6+ - Anti-detection plugin
- beautifulsoup4 4.12.0+ - HTML parsing
- tenacity 8.2.0+ - Retry logic (`prospect/scraper/serpapi.py`)

**Utilities:**
- click 8.1.0+ - CLI framework (`prospect/cli.py`)
- rich 13.0.0+ - Terminal formatting
- python-dotenv 1.0.0+ - Environment loading (`prospect/config.py`)
- PyYAML 6.0+ - YAML config parsing (`prospect/config.py`)
- Jinja2 3.1.2+ - Template rendering
- websockets 12.0+ - Real-time updates (`prospect/web/ws/`)

## Configuration

**Environment:**
- `.env` files with `.env.example` template
- Key vars: `SERPAPI_KEY`, `STRIPE_SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`
- YAML configuration for scoring weights (`config.example.yaml`)

**Build:**
- `pyproject.toml` - Build config, dependencies, tool settings
- `tsconfig.json` - Not applicable (no TypeScript)

## Platform Requirements

**Development:**
- macOS/Linux/Windows (any platform with Python 3.11+)
- Docker optional for local development
- SQLite for local database

**Production:**
- Railway deployment platform (`RAILWAY_ENVIRONMENT` detection)
- Persistent volume for SQLite: `/data/prospects.db`
- Procfile: `web: uvicorn prospect.web.app:app --host 0.0.0.0 --port ${PORT:-8000}`
- Docker support via `docker/Dockerfile`

---

*Stack analysis: 2026-02-01*
*Update after major dependency changes*
