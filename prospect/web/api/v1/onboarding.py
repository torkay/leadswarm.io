"""Onboarding API endpoints (stub for Phase 2 implementation)."""

from fastapi import APIRouter

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/status")
def get_onboarding_status():
    """
    Get onboarding status for current user.

    Stub endpoint - full implementation in Phase 2 (Onboarding Experience).
    """
    return {
        "completed": False,
        "steps": {
            "welcome_seen": False,
            "first_search": False,
            "score_explained": False,
        },
        "message": "Onboarding flow coming soon",
    }
