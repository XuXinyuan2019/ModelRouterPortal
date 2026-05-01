"""Usage tracking and balance deduction service."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.model import Model
from app.models.usage import UsageRecord
from app.models.user import User
from app.services import apikey_service
from app.services.billing_service import calculate_cost

logger = logging.getLogger(__name__)


def record_usage(
    db: Session,
    user_id: int,
    model_id: str,
    tokens_input: int,
    tokens_output: int,
    cost: float,
    request_type: str = "simulate",
) -> UsageRecord:
    """Create a usage record."""
    record = UsageRecord(
        user_id=user_id,
        model_id=model_id,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        cost=cost,
        request_type=request_type,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def deduct_balance(db: Session, user: User, amount: float) -> bool:
    """Atomically deduct balance. Returns True if successful."""
    if user.balance < amount:
        return False
    user.balance -= amount
    db.commit()
    return True


def check_and_enforce_balance_limit(db: Session, user: User) -> None:
    """If balance <= 0, disable all user's API keys on Alibaba Cloud."""
    if user.balance > 0:
        return
    if not user.client_id:
        return
    try:
        keys = apikey_service.list_api_keys(user.client_id)
        for key in keys:
            if key.get("status") == "active":
                key_id = key.get("id")
                if key_id is not None:
                    apikey_service.delete_api_key(key_id, user.client_id)
                    logger.info(
                        "Disabled API key %s for user %s due to zero balance",
                        key_id,
                        user.id,
                    )
    except Exception as e:
        logger.warning("Failed to disable API keys for user %s: %s", user.id, e)


def get_usage_overview(db: Session, user_id: int, days: int = 30) -> dict:
    """Aggregate usage overview for the given period."""
    since = datetime.utcnow() - timedelta(days=days)
    result = (
        db.query(
            func.coalesce(func.sum(UsageRecord.cost), 0.0).label("total_cost"),
            func.coalesce(
                func.sum(UsageRecord.tokens_input + UsageRecord.tokens_output), 0
            ).label("total_tokens"),
            func.count(UsageRecord.id).label("total_requests"),
        )
        .filter(UsageRecord.user_id == user_id, UsageRecord.created_at >= since)
        .first()
    )

    return {
        "total_cost": float(result.total_cost) if result else 0.0,
        "total_tokens": int(result.total_tokens) if result else 0,
        "total_requests": int(result.total_requests) if result else 0,
        "period": f"近{days}日",
    }


def get_usage_trend(db: Session, user_id: int, days: int = 7) -> list[dict]:
    """Daily usage trend for the given period."""
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            func.date(UsageRecord.created_at).label("date"),
            func.coalesce(func.sum(UsageRecord.cost), 0.0).label("cost"),
            func.coalesce(
                func.sum(UsageRecord.tokens_input + UsageRecord.tokens_output), 0
            ).label("tokens"),
            func.count(UsageRecord.id).label("requests"),
        )
        .filter(UsageRecord.user_id == user_id, UsageRecord.created_at >= since)
        .group_by(func.date(UsageRecord.created_at))
        .order_by(func.date(UsageRecord.created_at))
        .all()
    )

    return [
        {
            "date": str(row.date),
            "cost": float(row.cost),
            "tokens": int(row.tokens),
            "requests": int(row.requests),
        }
        for row in rows
    ]


def get_model_usage(db: Session, user_id: int, days: int = 30) -> list[dict]:
    """Per-model usage aggregation for the given period."""
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            UsageRecord.model_id,
            func.coalesce(func.sum(UsageRecord.cost), 0.0).label("cost"),
            func.coalesce(
                func.sum(UsageRecord.tokens_input + UsageRecord.tokens_output), 0
            ).label("tokens"),
            func.count(UsageRecord.id).label("requests"),
        )
        .filter(UsageRecord.user_id == user_id, UsageRecord.created_at >= since)
        .group_by(UsageRecord.model_id)
        .all()
    )

    # Get model names
    model_names = {m.model_id: m.name for m in db.query(Model).all()}

    return [
        {
            "model_id": row.model_id,
            "model_name": model_names.get(row.model_id, row.model_id),
            "cost": float(row.cost),
            "tokens": int(row.tokens),
            "requests": int(row.requests),
        }
        for row in rows
    ]
