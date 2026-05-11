from fastapi import APIRouter, HTTPException

from app.schemas.media import (
    AssetSearchRequest,
    AssetSearchResponse,
    BrollDownloadRequest,
    BrollDownloadResponse,
)
from app.services.broll_service import broll_service


router = APIRouter(prefix="/broll", tags=["broll"])


@router.post("/search", response_model=AssetSearchResponse)
def broll_search(request: AssetSearchRequest) -> AssetSearchResponse:
    if not request.keywords:
        raise HTTPException(status_code=400, detail="Palavras-chave sao obrigatorias.")

    try:
        return AssetSearchResponse(clips=broll_service.search(keywords=request.keywords, collection=request.collection))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/download", response_model=BrollDownloadResponse)
def broll_download(request: BrollDownloadRequest) -> BrollDownloadResponse:
    try:
        result = broll_service.download(url=str(request.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return BrollDownloadResponse(**result)
