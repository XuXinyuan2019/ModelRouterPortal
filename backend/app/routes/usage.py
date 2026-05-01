"""Usage & Dashboard routes — real SDK calls (TODO: implement)."""
from datetime import datetime

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_db
from app.models.activation import UserModelActivation
from app.models.user import User
from app.schemas.usage import (
    DashboardData,
    ModelUsageItem,
    UsageOverview,
    UsageTrendItem,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/usage", tags=["usage"])


@router.get("/overview", response_model=UsageOverview)
def usage_overview(
    current_user: User = Depends(get_current_user),
):
    # TODO: real SDK call
    return UsageOverview(total_cost=0, total_tokens=0, total_requests=0, period="")


@router.get("/trend", response_model=list[UsageTrendItem])
def usage_trend(
    current_user: User = Depends(get_current_user),
):
    # TODO: real SDK call
    return []


@router.get("/models", response_model=list[ModelUsageItem])
def usage_by_model(
    current_user: User = Depends(get_current_user),
):
    # TODO: real SDK call
    return []


# Dashboard endpoint — aggregates key metrics
dashboard_router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@dashboard_router.get("/", response_model=DashboardData)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activated_count = (
        db.query(UserModelActivation)
        .filter(
            UserModelActivation.user_id == current_user.id,
            UserModelActivation.status == "active",
        )
        .count()
    )

    return DashboardData(
        balance=current_user.balance,
        total_cost_30d=0,
        total_requests_30d=0,
        activated_models=activated_count,
        recent_trend=[],
    )
