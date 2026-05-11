from fastapi import APIRouter, Query

from app.schemas.usage import UsageByFeatureItem, UsageSummaryResponse
from app.services.usage_service import usage_service


router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/summary", response_model=UsageSummaryResponse)
def get_usage_summary(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
) -> UsageSummaryResponse:
    return UsageSummaryResponse(**usage_service.get_summary(start_date=start_date, end_date=end_date))


@router.get("/by-feature", response_model=list[UsageByFeatureItem])
def get_usage_by_feature(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
) -> list[UsageByFeatureItem]:
    return [
        UsageByFeatureItem(**item)
        for item in usage_service.get_by_feature(start_date=start_date, end_date=end_date)
    ]
