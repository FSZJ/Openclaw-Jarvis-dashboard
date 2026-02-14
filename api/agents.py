"""
Agents API routes - agent status and configuration
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth import AuthService
from services.collector import StatusCollector

router = APIRouter(prefix="/agents", tags=["Agents"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
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


@router.get("/")
async def get_agent_status(current_user: str = Depends(get_current_user)):
    """Get complete agent status"""
    collector = StatusCollector()
    return collector.get_agent_status()


@router.get("/main")
async def get_main_agent_config(current_user: str = Depends(get_current_user)):
    """Get main agent configuration"""
    collector = StatusCollector()
    return collector.get_agent_config()


@router.get("/models")
async def get_available_models(current_user: str = Depends(get_current_user)):
    """Get available models from configuration"""
    collector = StatusCollector()
    config = collector.get_agent_config()
    return {
        "provider": config.provider,
        "model": config.model,
        "providers": {k: {
            "name": v.name,
            "base_url": v.base_url,
            "models": [m.dict() for m in v.models]
        } for k, v in config.providers.items()}
    }


@router.get("/subagents")
async def get_subagent_runs(current_user: str = Depends(get_current_user)):
    """Get subagent run history"""
    collector = StatusCollector()
    return collector.get_subagent_runs()
