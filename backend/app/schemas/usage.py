from datetime import datetime

from pydantic import BaseModel


class UsageOverview(BaseModel):
    total_cost: float
    total_tokens: int
    total_requests: int
    period: str  # e.g. "2026-04"


class UsageTrendItem(BaseModel):
    date: str
    cost: float
    tokens: int
    requests: int


class ModelUsageItem(BaseModel):
    model_id: str
    model_name: str
    cost: float
    tokens: int
    requests: int


class DashboardData(BaseModel):
    balance: float
    total_cost_30d: float
    total_requests_30d: int
    activated_models: int
    recent_trend: list[UsageTrendItem]
