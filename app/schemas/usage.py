from pydantic import BaseModel


class UsageSummaryResponse(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_estimated_cost_usd: float
    projected_monthly_cost_usd: float
    active_days: int


class UsageByFeatureItem(BaseModel):
    feature: str
    provider: str
    start_date: str | None = None
    end_date: str | None = None
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_estimated_cost_usd: float
    projected_monthly_cost_usd: float
    active_days: int
