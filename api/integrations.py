"""Model integrations API."""
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth import AuthService
from services.integration_store import IntegrationStore
from services.usage_service import UsageService
from models import IntegrationsUpdateRequest

router = APIRouter(prefix="/integrations", tags=["Integrations"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    auth_service = AuthService()
    username = auth_service.verify_token(token)
    if not username:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


@router.get("/models")
async def get_model_integrations(current_user: str = Depends(get_current_user)):
    return IntegrationStore.get_public_view()


@router.put("/models")
async def update_model_integrations(payload: IntegrationsUpdateRequest, current_user: str = Depends(get_current_user)):
    IntegrationStore.update_all(payload.providers)
    UsageService.invalidate_cache()
    return {
        "success": True,
        "message": "模型配置已保存",
        "data": IntegrationStore.get_public_view(),
    }


@router.post("/models/{provider}/validate")
async def validate_model_integration(
    provider: str,
    payload: dict | None = Body(default=None),
    current_user: str = Depends(get_current_user)
):
    payload = payload or {}
    draft_config = payload.get("config") if isinstance(payload, dict) else None
    if draft_config is None and isinstance(payload, dict):
        draft_config = payload
    result = UsageService.validate_provider(provider, draft_config=draft_config if isinstance(draft_config, dict) else None)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message") or "验证失败")
    return result
