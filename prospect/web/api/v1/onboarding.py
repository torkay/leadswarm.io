"""Onboarding API endpoints for first-time user experience."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from prospect.web.database import get_db, User
from prospect.web.auth import get_current_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# Step definitions
ONBOARDING_STEPS = {
    0: "not_started",
    1: "welcome_seen",
    2: "first_search",
    3: "score_explained",
    4: "complete",
}

STEP_NAME_TO_NUMBER = {v: k for k, v in ONBOARDING_STEPS.items()}


class OnboardingStatus(BaseModel):
    """Current onboarding status for a user."""
    completed: bool
    current_step: int
    steps: dict


class OnboardingStepResponse(BaseModel):
    """Response after marking a step complete."""
    success: bool
    completed: bool
    current_step: int
    steps: dict


def get_steps_dict(current_step: int) -> dict:
    """Build steps dictionary showing completion status."""
    return {
        "welcome_seen": current_step >= 1,
        "first_search": current_step >= 2,
        "score_explained": current_step >= 3,
    }


@router.get("/status", response_model=OnboardingStatus)
def get_onboarding_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get onboarding status for current user.

    Returns:
        - completed: bool (from user.onboarding_completed)
        - current_step: int (from user.onboarding_step)
        - steps: dict with step names and completion status
    """
    return OnboardingStatus(
        completed=current_user.onboarding_completed,
        current_step=current_user.onboarding_step,
        steps=get_steps_dict(current_user.onboarding_step),
    )


@router.post("/step/{step_name}", response_model=OnboardingStepResponse)
def mark_step_complete(
    step_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark an onboarding step as complete.

    Valid step_names: welcome_seen, first_search, score_explained

    - Updates user.onboarding_step to appropriate number
    - If step 3 (score_explained) completed, sets onboarding_completed=True
    """
    valid_steps = ["welcome_seen", "first_search", "score_explained"]

    if step_name not in valid_steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid step name. Valid steps: {', '.join(valid_steps)}",
        )

    step_number = STEP_NAME_TO_NUMBER[step_name]

    # Only advance if this step is actually next (or later)
    # This prevents going backwards
    if step_number > current_user.onboarding_step:
        current_user.onboarding_step = step_number

        # If completing score_explained (step 3), mark onboarding complete
        if step_number == 3:
            current_user.onboarding_completed = True
            current_user.onboarding_step = 4  # complete

        db.commit()
        db.refresh(current_user)

    return OnboardingStepResponse(
        success=True,
        completed=current_user.onboarding_completed,
        current_step=current_user.onboarding_step,
        steps=get_steps_dict(current_user.onboarding_step),
    )


@router.post("/skip", response_model=OnboardingStepResponse)
def skip_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Skip onboarding entirely.

    Sets onboarding_completed=True and onboarding_step=4 (complete).
    """
    current_user.onboarding_completed = True
    current_user.onboarding_step = 4

    db.commit()
    db.refresh(current_user)

    return OnboardingStepResponse(
        success=True,
        completed=True,
        current_step=4,
        steps=get_steps_dict(4),
    )
