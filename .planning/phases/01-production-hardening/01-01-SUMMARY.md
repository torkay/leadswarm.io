---
phase: 01-production-hardening
plan: 01
subsystem: security
tags: [jwt, stripe, env-validation, fail-fast]

# Dependency graph
requires: []
provides:
  - Production startup validation for JWT_SECRET_KEY
  - Production startup validation for STRIPE_SECRET_KEY
  - Production startup validation for STRIPE_PRICE_* placeholders
  - Onboarding module stub for Phase 2
  - Complete .env.example documentation
affects: [02-onboarding-experience, deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fail-fast validation at import time"
    - "Environment-aware validation (dev vs production)"

key-files:
  created:
    - prospect/web/api/v1/onboarding.py
  modified:
    - prospect/web/auth.py
    - prospect/web/api/v1/billing.py
    - .env.example

key-decisions:
  - "Use RAILWAY_ENVIRONMENT or PRODUCTION env vars to detect production mode"
  - "Allow development without env vars (with warnings) for dev convenience"
  - "Validate Stripe price IDs by checking for price_1 prefix (real IDs) vs placeholders"

patterns-established:
  - "Fail-fast pattern: validate security config at import time, not request time"

issues-created: []

# Metrics
duration: 7min
completed: 2026-01-31
---

# Phase 1 Plan 1: Production Hardening Summary

**JWT secret validation, Stripe config validation, and onboarding module stub to ensure production fails fast on misconfiguration**

## Performance

- **Duration:** 7 min
- **Started:** 2026-01-31T17:16:35Z
- **Completed:** 2026-01-31T17:23:12Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- auth.py now validates JWT_SECRET_KEY at import time, fails in production if missing
- billing.py now validates STRIPE_SECRET_KEY and STRIPE_PRICE_* at import time
- Placeholder price IDs (price_scout_monthly) detected and rejected in production
- Development mode continues to work without env vars (with warnings)
- onboarding.py stub created to fix missing module import
- .env.example updated with all security-critical variables and generation instructions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add startup validation for security-critical env vars** - `cd30d43` (feat)
2. **Task 2: Create onboarding module stub and update .env.example** - `9f61764` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `prospect/web/auth.py` - Added JWT_SECRET_KEY validation with dev/prod awareness
- `prospect/web/api/v1/billing.py` - Added Stripe config validation at startup
- `prospect/web/api/v1/onboarding.py` - New stub module for Phase 2 onboarding
- `.env.example` - Added JWT_SECRET_KEY, STRIPE_*, APP_URL documentation

## Decisions Made

- Used RAILWAY_ENVIRONMENT or PRODUCTION env vars to detect production mode (matches existing Railway deployment)
- Development fallback uses warning instead of fatal error for dev convenience
- Stripe price ID validation checks for `price_1` prefix (real Stripe IDs) vs placeholder patterns

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- Production hardening complete for Phase 1
- Application will now fail fast on misconfigured security settings
- onboarding.py stub ready for Phase 2 implementation
- All security-critical env vars documented in .env.example

---
*Phase: 01-production-hardening*
*Completed: 2026-01-31*
