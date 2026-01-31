# External Integrations

**Analysis Date:** 2026-02-01

## APIs & External Services

**Search Engine API:**
- SerpAPI - Google Search results (Ads, Maps, Organic)
  - SDK/Client: httpx with custom client (`prospect/scraper/serpapi.py`)
  - Auth: `SERPAPI_KEY` environment variable
  - Features: Organic results, Google Maps results, Google Ads detection
  - Retry logic: tenacity with exponential backoff
  - Rate limits: Based on SerpAPI plan (100-5000 searches/month)

**Payment Processing:**
- Stripe - Subscription billing and payment processing
  - SDK/Client: stripe Python package (`prospect/web/api/v1/billing.py`)
  - Auth: `STRIPE_SECRET_KEY` environment variable
  - Features: Checkout sessions, customer portal, subscription management, webhooks
  - Webhook secret: `STRIPE_WEBHOOK_SECRET` for signature validation
  - Price IDs: `STRIPE_PRICE_SCOUT`, `STRIPE_PRICE_HUNTER`, `STRIPE_PRICE_COMMAND`
  - Tier mapping: scout ($99/mo), hunter ($149-249/mo), command ($499/mo)

**Email/SMS:**
- Not currently integrated
- Recommendation: SendGrid or Resend for transactional emails

## Data Storage

**Databases:**
- SQLite - Primary data store
  - Connection: `DATABASE_URL` env var or default `sqlite:///./prospects.db`
  - Railway: `sqlite:////data/prospects.db` (persistent volume)
  - Client: SQLAlchemy 2.0+ with aiosqlite driver
  - Migrations: Direct `Base.metadata.create_all()` (no Alembic)

**Tables:**
- User - User accounts with subscription tiers
- UsageRecord - Monthly usage tracking
- Search - Search history
- Prospect - Persisted prospect records
- Campaign - Search campaigns
- SearchConfig - Search depth configurations
- Job - Background job tracking

**File Storage:**
- Not currently used
- Local filesystem only for temp files

**Caching:**
- None (all database queries, no Redis)
- In-memory job state only (`prospect/web/state.py`)

## Authentication & Identity

**Auth Provider:**
- Custom JWT implementation (`prospect/web/auth.py`)
  - Algorithm: HS256
  - Expiration: 7 days
  - Secret key: `JWT_SECRET_KEY` environment variable
  - Token storage: Client-side (localStorage in frontend)

**Password Security:**
- bcrypt via passlib library
- Password hashing in `prospect/web/auth.py`

**OAuth Integrations:**
- None currently
- Potential: Google OAuth for simplified login

## Monitoring & Observability

**Error Tracking:**
- None configured
- Recommendation: Sentry for production

**Analytics:**
- None (planned)
- Detection signatures for Google Analytics, Facebook Pixel (for prospects)

**Logs:**
- stdout/stderr via Python logging
- Railway: Built-in log aggregation
- No structured logging service

## CI/CD & Deployment

**Hosting:**
- Railway - Primary deployment platform
  - Detection: `RAILWAY_ENVIRONMENT` environment variable
  - Persistent volume: `/data/` for SQLite database
  - Health check: Configured in Railway dashboard

**Deployment:**
- Procfile: `web: uvicorn prospect.web.app:app --host 0.0.0.0 --port ${PORT:-8000}`
- Docker support: `docker/Dockerfile`, `docker-compose.yml`
- Environment vars: Configured in Railway dashboard

**CI Pipeline:**
- Not configured (manual deployment)
- Recommendation: GitHub Actions for test/lint/deploy

## Environment Configuration

**Development:**
- Required env vars: `SERPAPI_KEY`
- Optional: `JWT_SECRET_KEY` (has weak dev default), `DATABASE_URL`
- Secrets location: `.env` (gitignored), `.env.example` for template
- Mock/stub services: SerpAPI has test mode, Stripe test mode

**Staging:**
- Not currently configured
- Recommendation: Separate Railway environment

**Production:**
- Secrets management: Railway environment variables
- Required env vars:
  - `SERPAPI_KEY` - Search API access
  - `JWT_SECRET_KEY` - Token signing (CRITICAL: must be set)
  - `STRIPE_SECRET_KEY` - Payment processing
  - `STRIPE_WEBHOOK_SECRET` - Webhook validation
  - `STRIPE_PRICE_SCOUT`, `STRIPE_PRICE_HUNTER`, `STRIPE_PRICE_COMMAND` - Price IDs
  - `APP_URL` - Application URL for redirects

## Webhooks & Callbacks

**Incoming:**
- Stripe webhooks - `/api/v1/billing/webhook`
  - Verification: Signature validation via `stripe.Webhook.construct_event()`
  - Events handled:
    - `checkout.session.completed` - Initial subscription
    - `customer.subscription.updated` - Tier changes
    - `customer.subscription.deleted` - Cancellations
    - `invoice.paid` - Successful payments
    - `invoice.payment_failed` - Failed payments

**Outgoing:**
- None currently

## Google Services

**Google Sheets API:**
- Export functionality (`prospect/sheets/client.py`)
- Authentication: Service account credentials (`prospect/sheets/auth.py`)
- Features: Create sheets, append data, formatting, sharing, link generation
- Scopes:
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/drive.file`
- Credential sources:
  - `GOOGLE_SHEETS_CREDENTIALS` (JSON string) - Production
  - `GOOGLE_SHEETS_CREDENTIALS_FILE` (file path) - Local dev
  - Default: `~/.config/prospect-command-center/credentials.json`

## Technology Detection (Outbound Analysis)

**CMS Detection:**
- WordPress, Wix, Squarespace, Shopify, Webflow, Weebly, GoDaddy, Joomla, Drupal
- Signatures in `prospect/config.py` (CMS_SIGNATURES)

**Tracking Detection:**
- Google Analytics, Facebook Pixel
- Booking systems: Calendly, Acuity, YouCanBook.Me, Setmore, Square, Fresha, HubSpot, etc.
- Signatures in `prospect/config.py`

**Domain Filtering:**
- 100+ directory domains filtered (Yelp, Yellow Pages, LinkedIn, etc.)
- `prospect/config.py` (DIRECTORY_DOMAINS)

## Real-Time Communication

**WebSockets:**
- Job status updates (`prospect/web/ws/jobs.py`)
- Used for search progress in frontend
- Protocol: Native WebSocket via FastAPI

## Export Capabilities

**Built-in:**
- CSV export
- JSON export
- Google Sheets export (with formatting and sharing)

**Location:**
- `prospect/export.py` - CSV/JSON
- `prospect/sheets/client.py` - Google Sheets

---

*Integration audit: 2026-02-01*
*Update when adding/removing external services*
