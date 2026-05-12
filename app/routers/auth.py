from fastapi import APIRouter, Request

from app.schemas.auth import AuthLoginRequest, AuthStatusResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthStatusResponse)
def login(request: Request, payload: AuthLoginRequest) -> AuthStatusResponse:
    request.session["gemini_api_key"] = payload.gemini_api_key.strip()
    return AuthStatusResponse(authenticated=True)


@router.get("/status", response_model=AuthStatusResponse)
def status(request: Request) -> AuthStatusResponse:
    authenticated = bool(str(request.session.get("gemini_api_key") or "").strip())
    return AuthStatusResponse(authenticated=authenticated)


@router.post("/logout", response_model=AuthStatusResponse)
def logout(request: Request) -> AuthStatusResponse:
    request.session.pop("gemini_api_key", None)
    return AuthStatusResponse(authenticated=False)
