"""Usage & Dashboard routes — real data from usage_records."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.activation import UserModelActivation
from app.models.user import User
from app.schemas.usage import (
    DashboardData,
    ModelUsageItem,
    UsageOverview,
    UsageTrendItem,
)
from app.services import usage_service

router = APIRouter(prefix="/api/v1/usage", tags=["usage"])


@router.get("/overview", response_model=UsageOverview)
def usage_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = usage_service.get_usage_overview(db, current_user.id, days=30)
    return UsageOverview(**data)


@router.get("/trend", response_model=list[UsageTrendItem])
def usage_trend(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = usage_service.get_usage_trend(db, current_user.id, days=7)
    return [UsageTrendItem(**r) for r in rows]


@router.get("/models", response_model=list[ModelUsageItem])
def usage_by_model(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = usage_service.get_model_usage(db, current_user.id, days=30)
    return [ModelUsageItem(**r) for r in rows]


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

    overview = usage_service.get_usage_overview(db, current_user.id, days=30)
    trend = usage_service.get_usage_trend(db, current_user.id, days=7)

    return DashboardData(
        balance=current_user.balance,
        total_cost_30d=overview["total_cost"],
        total_requests_30d=overview["total_requests"],
        activated_models=activated_count,
        recent_trend=[UsageTrendItem(**r) for r in trend],
    )
