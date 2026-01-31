# Prospect Command Center

## What This Is

A B2B lead intelligence tool for Australian marketing agencies. Search Google for local businesses, enrich with website signals, and score prospects based on who actually NEEDS marketing help — not just who exists. Turns hours of manual prospecting into minutes of prioritized leads.

## Core Value

**Find businesses that NEED marketing help — not just businesses that exist.** The Opportunity Score identifies prospects with marketing gaps (no analytics, no booking system, DIY CMS, slow site) who have budget (running Google Ads) and room to grow (poor SERP position). This is the differentiated value that competitors don't offer.

## Requirements

### Validated

<!-- Shipped and confirmed working. -->

- ✓ User authentication (JWT, registration, login) — existing
- ✓ Stripe billing (checkout, webhooks, 3 subscription tiers) — existing
- ✓ Usage tracking + monthly limits per tier — existing
- ✓ Google search via SerpAPI (Ads, Maps, Organic results) — existing
- ✓ Website enrichment (CMS detection, tracking pixels, booking systems) — existing
- ✓ Fit Score + Opportunity Score + Priority Score — existing
- ✓ Export to CSV, JSON, Google Sheets — existing
- ✓ Basic prospect list view with sorting/filtering — existing
- ✓ PWA-capable frontend (offline-ready) — existing

### Active

<!-- Current scope. Building toward these for v1 monetization. -->

- [ ] Onboarding flow (welcome modal, guided first search, score explanations)
- [ ] Better score visibility (expand opportunity notes, visual score breakdowns)
- [ ] Pipeline/CRM features (prospect status, follow-ups, campaign assignment)
- [ ] Outreach templates (email/phone scripts based on opportunity signals)
- [ ] ROI tracking (mark deals won from PCC leads, cost-per-lead calculation)
- [ ] Production hardening (fix JWT secret defaults, Stripe env validation)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Team/multi-user accounts — complexity for v1, single-user focus first
- Chrome extension — nice-to-have, not blocking monetization
- API access for customers — future expansion, not v1 priority

## Context

**Target market:**
- Australian marketing agencies (5-50 employees)
- Do local business prospecting
- Currently using manual Google searches + spreadsheets
- Budget: $99-499/month for tools

**Beta launch goal:**
- 10 founding member agencies at $149/month
- $1,490 MRR target
- 12-month commitment for locked "forever" rate

**Competitive positioning:**
- ZoomInfo: $15k+/year, poor AU data → PCC is 10x cheaper, AU-first
- Apollo: Per-seat pricing, no website intel → PCC has Opportunity Score
- Leadfeeder: No opportunity scoring, EU-focused → PCC is AU-first + scores leads
- Hunter: Email only, no context → PCC provides full intelligence

**Existing documentation:**
- `BETA_LAUNCH_PLAN.md` — 8-week build + sell plan
- `SPEC.md` — Technical specification
- `docs/product/pcc-onboarding-flow.md` — Onboarding UX spec
- `docs/research/pcc-competitive-analysis.md` — Market positioning
- `docs/research/pcc-pricing-optimization.md` — Pricing strategy
- `.planning/codebase/` — 7 codebase analysis documents

**Known issues (from codebase mapping):**
- Weak JWT secret fallback in production (`prospect/web/auth.py`)
- Hardcoded Stripe price ID defaults (`prospect/web/api/v1/billing.py`)
- Missing onboarding module import (`prospect/web/api/v1/router.py`)
- N+1 database queries in dashboard endpoints
- No tests for billing/webhook logic

## Constraints

- **Stack**: Python 3.11, FastAPI, SQLAlchemy, SQLite (existing — no migration)
- **Hosting**: Railway (existing deployment infrastructure)
- **Frontend**: Vanilla JS SPA with Tailwind (no framework migration)
- **Search API**: SerpAPI (usage-based cost, already integrated)

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Single-user focus for v1 | Reduces complexity, faster to market | — Pending |
| Vanilla JS over React | Existing code, PWA works, no build step | ✓ Good |
| SQLite on Railway | Simplest ops for beta, upgrade to PG later if needed | — Pending |
| Opportunity Score as core differentiator | Competitors don't have it, solves real problem | — Pending |

---
*Last updated: 2026-02-01 after initialization*
