from pydantic import BaseModel


class BillingRuleResponse(BaseModel):
    model_id: str
    input_price: float
    output_price: float
    unit: str = "1K tokens"
