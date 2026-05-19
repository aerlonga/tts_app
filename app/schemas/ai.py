from pydantic import BaseModel, Field


class GenerateAIRequest(BaseModel):
    prompt: str = Field(min_length=1)
    api_key: str | None = None
    model: str = "gemini-3-flash"
    system_instruction: str | None = None
    temperature: float = 0.7
    feature: str = "generic_generation"


class AIUsageSummary(BaseModel):
    log_id: int | None = None
    feature: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


class GenerateAIResponse(BaseModel):
    text: str
    usage: AIUsageSummary


class AssistantRequest(BaseModel):
    prompt: str = Field(min_length=1)
    api_key: str | None = None
    task_type: str = "strategy"
    preferred_provider: str | None = None
    max_context_docs: int = 5


class AssistantContextItem(BaseModel):
    doc_id: str
    source_type: str
    title: str
    score: float
    snippet: str


class AssistantResponse(BaseModel):
    answer: str
    provider_used: str
    model_used: str
    routing_reason: str
    context: list[AssistantContextItem]
    usage: AIUsageSummary
