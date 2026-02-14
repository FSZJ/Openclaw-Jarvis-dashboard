"""
Dashboard API route - aggregated payload for first paint.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth import AuthService
from services.collector import StatusCollector

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
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


@router.get("")
async def get_dashboard(light: bool = False, current_user: str = Depends(get_current_user)):
    """Get aggregated dashboard payload for first paint."""
    collector = StatusCollector()
    return collector.get_full_status(light=light)
