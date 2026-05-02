from datetime import datetime

from pydantic import BaseModel


class UsageOverview(BaseModel):
    total_cost: float
    total_tokens: int
    total_requests: int
    period: str  # e.g. "近30日"


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
    input_tokens: int = 0
    output_tokens: int = 0


class ModelDetailRow(BaseModel):
    timestamp: str
    total_calls: int
    all_tokens: int
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    total_amount: float


class ModelDetailData(BaseModel):
    rows: list[ModelDetailRow]
    total: int
    page: int
    page_size: int
    model_id: int | None = None
    model_name: str | None = None
    granularity: str = "daily"


class DashboardData(BaseModel):
    balance: float
    total_cost_30d: float
    total_requests_30d: int
    activated_models: int
    recent_trend: list[UsageTrendItem]


class UsageRecordResponse(BaseModel):
    id: int
    user_id: int
    model_id: str
    tokens_input: int
    tokens_output: int
    cost: float
    request_type: str
    created_at: datetime

    model_config = {"from_attributes": True}
