from fastapi import APIRouter, HTTPException, Request

from app.core.auth import resolve_gemini_api_key
from app.schemas.ideas import GenerateIdeasRequest, GenerateIdeasResponse, IdeaItem
from app.services.idea_service import idea_service


router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.post("/generate", response_model=GenerateIdeasResponse)
def generate_ideas(request: Request, payload: GenerateIdeasRequest) -> GenerateIdeasResponse:
    try:
        result = idea_service.generate_ideas(
            topic=payload.topic,
            platforms=payload.platforms,
            content_type=payload.content_type,
            language=payload.language,
            quantity=payload.quantity,
            force=payload.force,
            api_key=resolve_gemini_api_key(request, payload.api_key),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return GenerateIdeasResponse(
        ideas=[IdeaItem(**item) for item in result["ideas"]],
        from_cache=result["from_cache"],
    )
