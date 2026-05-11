from fastapi import APIRouter, HTTPException, Query

from app.schemas.analytics import (
    AnalyticsChannelSummary,
    AnalyticsChannelSummaryResponse,
    AnalyticsVideoDetailResponse,
    AnalyticsVideoMetric,
    AnalyticsVideosResponse,
)
from app.services.youtube_analytics_service import youtube_analytics_service


router = APIRouter(prefix="/analytics/youtube", tags=["analytics"])


@router.get("/channel-summary", response_model=AnalyticsChannelSummaryResponse)
def get_channel_summary(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
) -> AnalyticsChannelSummaryResponse:
    try:
        result = youtube_analytics_service.get_channel_summary(start_date=start_date, end_date=end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return AnalyticsChannelSummaryResponse(item=AnalyticsChannelSummary(**result))


@router.get("/videos", response_model=AnalyticsVideosResponse)
def list_video_metrics(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    max_results: int = Query(10, ge=1, le=50),
) -> AnalyticsVideosResponse:
    try:
        result = youtube_analytics_service.list_video_metrics(
            start_date=start_date,
            end_date=end_date,
            max_results=max_results,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return AnalyticsVideosResponse(
        start_date=result["start_date"],
        end_date=result["end_date"],
        count=result["count"],
        items=[AnalyticsVideoMetric(**item) for item in result["items"]],
    )


@router.get("/videos/{video_id}", response_model=AnalyticsVideoDetailResponse)
def get_video_metrics(
    video_id: str,
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
) -> AnalyticsVideoDetailResponse:
    try:
        result = youtube_analytics_service.get_video_metrics(
            video_id=video_id,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return AnalyticsVideoDetailResponse(
        start_date=result["start_date"],
        end_date=result["end_date"],
        item=AnalyticsVideoMetric(**result["item"]),
    )
