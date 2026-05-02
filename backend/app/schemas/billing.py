from pydantic import BaseModel


class BillingTierResponse(BaseModel):
    input_price: float
    output_price: float
    min_tokens: int
    max_tokens: int


class BillingRuleResponse(BaseModel):
    model_id: str
    tiers: list[BillingTierResponse]
    unit: str = "百万 tokens"
