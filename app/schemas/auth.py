from pydantic import BaseModel, Field


class AuthLoginRequest(BaseModel):
    gemini_api_key: str = Field(min_length=1)


class AuthStatusResponse(BaseModel):
    authenticated: bool
