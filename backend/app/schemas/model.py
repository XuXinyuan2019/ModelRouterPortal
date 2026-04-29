from datetime import datetime

from pydantic import BaseModel


class ModelResponse(BaseModel):
    id: int
    model_id: str
    name: str
    description: str | None
    model_type: str
    provider: str
    icon_url: str | None
    is_available: bool
    sort_order: int

    model_config = {"from_attributes": True}


class ModelDetailResponse(ModelResponse):
    activated: bool = False


class ActivationResponse(BaseModel):
    id: int
    user_id: int
    model_id: str
    status: str
    activated_at: datetime
    deactivated_at: datetime | None

    model_config = {"from_attributes": True}
