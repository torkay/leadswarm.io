# Codebase Concerns

**Analysis Date:** 2026-02-01

## Tech Debt

**Hardcoded Stripe Price IDs with Insecure Fallbacks:**
- Issue: Uses placeholder price IDs (`price_scout_monthly`) when env vars missing
- Files: `prospect/web/api/v1/billing.py:25-29`
- Why: Quick implementation without proper env validation
- Impact: Could allow transactions at wrong prices if env vars not set
- Fix approach: Fail fast at startup if `STRIPE_PRICE_*` vars not configured

**Weak Default JWT Secret:**
- Issue: Falls back to `"dev-secret-key-change-in-production"` if env var missing
- Files: `prospect/web/auth.py:17`
- Why: Developer convenience for local testing
- Impact: Token forgery possible if production forgets to set `JWT_SECRET_KEY`
- Fix approach: Raise error at startup if `JWT_SECRET_KEY` not set in production

**No Database Migration Strategy:**
- Issue: Direct `Base.metadata.create_all()` instead of proper migrations
- Files: `prospect/web/database.py:455`
- Why: SQLite-first development, quick iteration
- Impact: Schema changes break production without rollback capability
- Fix approach: Add Alembic migrations, especially before PostgreSQL switch

**Missing Environment Variable Documentation:**
- Issue: `.env.example` incomplete - missing critical vars
- Files: `.env.example`
- Why: Variables added incrementally without updating template
- Impact: Production deployments may fail or have security issues
- Fix approach: Document all required vars: `JWT_SECRET_KEY`, `STRIPE_*`, `APP_URL`

## Known Bugs

**Orphaned else clause in app.py:**
- Symptoms: Unreachable code at line 97
- Trigger: Code inspection (not runtime error currently)
- Files: `prospect/web/app.py:97`
- Workaround: None needed (code is ignored)
- Root cause: Incomplete refactoring left stray `else:` clause
- Fix: Remove orphaned line

**Missing onboarding module import:**
- Symptoms: ImportError on application startup (if onboarding router included)
- Trigger: Starting the application
- Files: `prospect/web/api/v1/router.py:5`
- Workaround: Module not currently included in router (commented out or conditional)
- Root cause: Incomplete migration or deleted file
- Fix: Create `onboarding.py` or remove import

## Security Considerations

**Stripe Webhook Secret Validation Gap:**
- Risk: If `STRIPE_WEBHOOK_SECRET` not set, endpoint returns 500 instead of rejecting
- Files: `prospect/web/api/v1/billing.py:160-165`
- Current mitigation: Stripe signature validation exists when secret is set
- Recommendations: Validate secret exists at startup, fail fast if missing

**Admin Role Check Missing Server Verification:**
- Risk: No admin functionality currently, but pattern for future
- Files: Not applicable yet
- Current mitigation: No admin features implemented
- Recommendations: Add middleware-level role verification before adding admin features

**Incomplete Environment Configuration:**
- Risk: Production could run with dev defaults for security-critical values
- Files: `prospect/web/auth.py`, `prospect/web/api/v1/billing.py`
- Current mitigation: None (dev defaults used)
- Recommendations: Startup validation for all security-critical env vars

## Performance Bottlenecks

**N+1 Queries in Dashboard:**
- Problem: 9+ separate count queries for dashboard summary
- Files: `prospect/web/api/v1/dashboard.py:15-116`
- Measurement: Not profiled, but linear scaling with data
- Cause: Individual COUNT queries instead of combined CTEs
- Improvement path: Combine into 3-4 queries with CTEs or subqueries

**N+1 Queries in Insights:**
- Problem: 6+ separate queries for insight calculations
- Files: `prospect/web/api/v1/dashboard.py:184-302`
- Measurement: Not profiled
- Cause: Sequential database calls for each insight type
- Improvement path: Batch queries with window functions

**Score Distribution Query:**
- Problem: Fetches ALL prospect scores into memory, processes in Python
- Files: `prospect/web/api/v1/dashboard.py:305-345`
- Measurement: Memory usage scales with prospect count
- Cause: Bucketing done in Python instead of SQL
- Improvement path: Use GROUP BY with CASE buckets in SQL

**Missing Database Indexes:**
- Problem: No explicit indexes on foreign keys or query columns
- Files: `prospect/web/database.py`
- Measurement: Queries slow at scale
- Cause: Initial development without optimization
- Improvement path: Add indexes on `Search.user_id`, `Campaign.user_id`, `Prospect.domain`

## Fragile Areas

**Usage Limit Race Condition:**
- Why fragile: Check and increment are not atomic
- Files: `prospect/web/api/v1/usage.py:237-255`
- Common failures: Concurrent requests could exceed limits
- Safe modification: Use database-level locking or atomic update
- Test coverage: Not tested for concurrent access

**Stripe Metadata Assumptions:**
- Why fragile: Assumes `user_id` always exists in checkout metadata
- Files: `prospect/web/api/v1/billing.py:214-215`
- Common failures: Webhook fails if metadata corrupted
- Safe modification: Add fallback handling for missing metadata
- Test coverage: No webhook tests

**Empty Prospects API:**
- Why fragile: File exists but is empty
- Files: `prospect/web/api/v1/prospects.py`
- Common failures: 404 for expected endpoints
- Safe modification: Implement or remove from router
- Test coverage: None

## Scaling Limits

**SQLite Single-Writer:**
- Current capacity: ~100 concurrent users comfortably
- Limit: Write contention under high load
- Symptoms at limit: Database locked errors
- Scaling path: Migrate to PostgreSQL for production

**In-Memory Job State:**
- Current capacity: ~1000 active jobs
- Limit: Memory usage, no persistence across restarts
- Symptoms at limit: Lost job state on deploy
- Scaling path: Redis for job state, or database-backed queue

## Dependencies at Risk

**No Critical Dependency Risks Identified**
- All major dependencies actively maintained
- Stripe, SQLAlchemy, FastAPI have stable APIs

## Missing Critical Features

**Payment Failure Handling:**
- Problem: No retry mechanism or user notification for failed payments
- Current workaround: Users manually retry
- Blocks: Proper subscription lifecycle management
- Implementation complexity: Medium (webhook handling + email)

**Email Notifications:**
- Problem: No transactional email integration
- Current workaround: None
- Blocks: Password reset, subscription alerts, usage warnings
- Implementation complexity: Low (add SendGrid/Resend)

## Test Coverage Gaps

**Billing/Payment Flow:**
- What's not tested: Stripe webhook processing, subscription tier updates
- Files: `prospect/web/api/v1/billing.py`
- Risk: Payment logic regressions undetected
- Priority: High
- Difficulty: Need Stripe test fixtures and webhook simulation

**Usage Limit Enforcement:**
- What's not tested: Concurrent limit checks, race conditions
- Files: `prospect/web/api/v1/usage.py`
- Risk: Users could exceed limits
- Priority: Medium
- Difficulty: Needs concurrent test harness

**Error Boundary Behavior:**
- What's not tested: API error responses for edge cases
- Risk: Unhandled exceptions expose stack traces
- Priority: Medium
- Difficulty: Low (add error case tests)

---

*Concerns audit: 2026-02-01*
*Update as issues are fixed or new ones discovered*
