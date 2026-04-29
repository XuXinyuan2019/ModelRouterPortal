"""Usage & Dashboard routes — mock data in MOCK_MODE, real SDK calls otherwise."""
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.config import settings
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

# Mock model names
_MODEL_NAMES = {
    "qwen3.6-plus": "Qwen3.6-Plus",
    "qwen3-max": "Qwen3-Max",
    "kimi-k2.6": "Kimi-K2.6",
    "deepseek-v4-pro": "DeepSeek-V4-Pro",
}


def _mock_trend(days: int = 7) -> list[UsageTrendItem]:
    today = datetime.utcnow().date()
    result = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        cost = round(random.uniform(0.5, 15.0), 2)
        tokens = random.randint(1000, 50000)
        requests = random.randint(5, 200)
        result.append(
            UsageTrendItem(
                date=d.isoformat(),
                cost=cost,
                tokens=tokens,
                requests=requests,
            )
        )
    return result


def _mock_model_usage() -> list[ModelUsageItem]:
    return [
        ModelUsageItem(
            model_id=mid,
            model_name=name,
            cost=round(random.uniform(5.0, 100.0), 2),
            tokens=random.randint(10000, 500000),
            requests=random.randint(50, 2000),
        )
        for mid, name in _MODEL_NAMES.items()
    ]


@router.get("/overview", response_model=UsageOverview)
def usage_overview(
    current_user: User = Depends(get_current_user),
):
    if settings.MOCK_MODE:
        return UsageOverview(
            total_cost=round(random.uniform(20.0, 200.0), 2),
            total_tokens=random.randint(100000, 1000000),
            total_requests=random.randint(500, 5000),
            period=datetime.utcnow().strftime("%Y-%m"),
        )
    # TODO: real SDK call
    return UsageOverview(total_cost=0, total_tokens=0, total_requests=0, period="")


@router.get("/trend", response_model=list[UsageTrendItem])
def usage_trend(
    days: int = Query(default=7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
):
    if settings.MOCK_MODE:
        return _mock_trend(days)
    return []


@router.get("/models", response_model=list[ModelUsageItem])
def usage_by_model(
    current_user: User = Depends(get_current_user),
):
    if settings.MOCK_MODE:
        return _mock_model_usage()
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

    trend = _mock_trend(7) if settings.MOCK_MODE else []
    total_cost = round(sum(t.cost for t in trend), 2)
    total_requests = sum(t.requests for t in trend)

    return DashboardData(
        balance=current_user.balance,
        total_cost_30d=total_cost,
        total_requests_30d=total_requests,
        activated_models=activated_count,
        recent_trend=trend,
    )
