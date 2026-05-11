from fastapi import APIRouter, HTTPException

from app.schemas.ai import (
    AIUsageSummary,
    AssistantContextItem,
    AssistantRequest,
    AssistantResponse,
    GenerateAIRequest,
    GenerateAIResponse,
)
from app.services.ai_assistant_service import ai_assistant_service
from app.services.gemini_service import gemini_service


router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate", response_model=GenerateAIResponse)
def generate_ai(request: GenerateAIRequest) -> GenerateAIResponse:
    try:
        result = gemini_service.generate_text(
            feature=request.feature,
            contents=request.prompt,
            api_key=request.api_key,
            model=request.model,
            system_instruction=request.system_instruction,
            temperature=request.temperature,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    usage = result["usage"]
    return GenerateAIResponse(
        text=result["text"],
        usage=AIUsageSummary(
            log_id=usage.get("id"),
            feature=usage["feature"],
            provider=usage["provider"],
            model=usage["model"],
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            estimated_cost_usd=usage.get("estimated_cost_usd", 0.0),
        ),
    )


@router.post("/assistant", response_model=AssistantResponse)
def assistant(request: AssistantRequest) -> AssistantResponse:
    try:
        result = ai_assistant_service.ask(
            prompt=request.prompt,
            task_type=request.task_type,
            preferred_provider=request.preferred_provider,
            api_key=request.api_key,
            max_context_docs=request.max_context_docs,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    usage = result["usage"]
    return AssistantResponse(
        answer=result["answer"],
        provider_used=result["provider_used"],
        model_used=result["model_used"],
        routing_reason=result["routing_reason"],
        context=[AssistantContextItem(**item) for item in result["context"]],
        usage=AIUsageSummary(
            log_id=usage.get("id"),
            feature=usage["feature"],
            provider=usage["provider"],
            model=usage["model"],
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            estimated_cost_usd=usage.get("estimated_cost_usd", 0.0),
        ),
    )
