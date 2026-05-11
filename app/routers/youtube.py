from fastapi import APIRouter, HTTPException, Query

from app.schemas.youtube import (
    YouTubeChannelItem,
    YouTubeChannelResponse,
    YouTubeSearchResponse,
    YouTubeVideoItem,
    YouTubeVideoResponse,
)
from app.services.youtube_data_service import youtube_data_service


router = APIRouter(prefix="/youtube", tags=["youtube"])


@router.get("/search", response_model=YouTubeSearchResponse)
def search_youtube(
    q: str = Query(..., min_length=1),
    max_results: int = Query(10, ge=1, le=25),
    order: str = Query("relevance"),
) -> YouTubeSearchResponse:
    try:
        result = youtube_data_service.search(query=q, max_results=max_results, order=order)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return YouTubeSearchResponse(
        query=result["query"],
        order=result["order"],
        count=result["count"],
        from_cache=result["from_cache"],
        items=[YouTubeVideoItem(**item) for item in result["items"]],
    )


@router.get("/videos/{video_id}", response_model=YouTubeVideoResponse)
def get_youtube_video(video_id: str) -> YouTubeVideoResponse:
    try:
        result = youtube_data_service.get_video(video_id=video_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return YouTubeVideoResponse(from_cache=result["from_cache"], item=YouTubeVideoItem(**result["item"]))


@router.get("/channels/{channel_id}", response_model=YouTubeChannelResponse)
def get_youtube_channel(channel_id: str) -> YouTubeChannelResponse:
    try:
        result = youtube_data_service.get_channel(channel_id=channel_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return YouTubeChannelResponse(from_cache=result["from_cache"], item=YouTubeChannelItem(**result["item"]))
