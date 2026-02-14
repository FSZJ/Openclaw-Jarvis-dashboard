"""Usage panels API."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth import AuthService
from services.usage_service import UsageService

router = APIRouter(prefix="/usage", tags=["Usage"])
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


@router.get("/panels")
async def get_usage_panels(current_user: str = Depends(get_current_user)):
    return {"panels": UsageService.get_usage_panels()}
