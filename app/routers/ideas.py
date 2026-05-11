from fastapi import APIRouter, HTTPException

from app.schemas.ideas import GenerateIdeasRequest, GenerateIdeasResponse, IdeaItem
from app.services.idea_service import idea_service


router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.post("/generate", response_model=GenerateIdeasResponse)
def generate_ideas(request: GenerateIdeasRequest) -> GenerateIdeasResponse:
    try:
        result = idea_service.generate_ideas(
            topic=request.topic,
            platforms=request.platforms,
            content_type=request.content_type,
            language=request.language,
            quantity=request.quantity,
            force=request.force,
            api_key=request.api_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return GenerateIdeasResponse(
        ideas=[IdeaItem(**item) for item in result["ideas"]],
        from_cache=result["from_cache"],
    )
