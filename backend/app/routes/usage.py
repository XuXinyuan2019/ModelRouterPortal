"""Usage & Dashboard routes — real data from Alibaba Cloud Cost APIs."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.activation import UserModelActivation
from app.models.user import User
from app.schemas.usage import (
    DashboardData,
    ModelDetailData,
    ModelUsageItem,
    UsageOverview,
    UsageTrendItem,
)
from app.services import cost_service

router = APIRouter(prefix="/api/v1/usage", tags=["usage"])


@router.get("/overview", response_model=UsageOverview)
def usage_overview(current_user: User = Depends(get_current_user)):
    if not current_user.client_id:
        return UsageOverview(total_cost=0.0, total_tokens=0, total_requests=0, period="近30日")
    data = cost_service.get_cost_overview(current_user.client_id, days=30)
    return UsageOverview(**data)


@router.get("/trend", response_model=list[UsageTrendItem])
def usage_trend(
    days: int = 7,
    current_user: User = Depends(get_current_user),
):
    if not current_user.client_id:
        return []
    rows = cost_service.get_cost_trend(current_user.client_id, days=days)
    return [UsageTrendItem(**r) for r in rows]


@router.get("/models", response_model=list[ModelUsageItem])
def usage_by_model(current_user: User = Depends(get_current_user)):
    if not current_user.client_id:
        return []
    rows = cost_service.get_cost_model_list(current_user.client_id, days=30)
    return [ModelUsageItem(**r) for r in rows]


@router.get("/models/{model_id}", response_model=ModelDetailData)
def usage_model_detail(
    model_id: int,
    days: int = 30,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
):
    if not current_user.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定阿里云客户端 / Alibaba Cloud client not bound",
        )
    data = cost_service.get_cost_model_detail(
        current_user.client_id, model_id, days=days,
        page_index=page, page_size=page_size,
    )
    return ModelDetailData(**data)


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

    if current_user.client_id:
        overview = cost_service.get_cost_overview(current_user.client_id, days=30)
        trend = cost_service.get_cost_trend(current_user.client_id, days=7)
    else:
        overview = {"total_cost": 0.0, "total_requests": 0}
        trend = []

    return DashboardData(
        balance=current_user.balance,
        total_cost_30d=overview["total_cost"],
        total_requests_30d=overview.get("total_requests", 0),
        activated_models=activated_count,
        recent_trend=[UsageTrendItem(**r) for r in trend],
    )
