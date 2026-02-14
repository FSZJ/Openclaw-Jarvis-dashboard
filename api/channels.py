"""
Channels API routes - channel status and configuration
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth import AuthService
from services.collector import StatusCollector

router = APIRouter(prefix="/channels", tags=["Channels"])
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
async def get_channel_status(current_user: str = Depends(get_current_user)):
    """Get all channel statuses"""
    collector = StatusCollector()
    return collector.get_channel_status()


@router.get("/telegram")
async def get_telegram_status(current_user: str = Depends(get_current_user)):
    """Get Telegram channel status"""
    collector = StatusCollector()
    status = collector.get_channel_status()
    return status.telegram


@router.get("/imessage")
async def get_imessage_status(current_user: str = Depends(get_current_user)):
    """Get iMessage channel status"""
    collector = StatusCollector()
    status = collector.get_channel_status()
    return status.imessage
