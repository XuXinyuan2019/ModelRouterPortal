from datetime import datetime

from pydantic import BaseModel, Field


class BalanceResponse(BaseModel):
    balance: float


class RechargeRequest(BaseModel):
    amount: float = Field(..., gt=0, le=100000)
    remark: str | None = None


class RechargeRecordResponse(BaseModel):
    id: int
    amount: float
    balance_before: float
    balance_after: float
    status: str
    remark: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
