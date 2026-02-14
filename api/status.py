"""
Status API routes - system health and status
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth import AuthService
from services.collector import StatusCollector

router = APIRouter(prefix="/status", tags=["Status"])
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
async def get_status(light: bool = False, current_user: str = Depends(get_current_user)):
    """Get complete system status"""
    collector = StatusCollector()
    return collector.get_full_status(light=light)


@router.get("/system")
async def get_system_health(current_user: str = Depends(get_current_user)):
    """Get system health metrics"""
    collector = StatusCollector()
    return collector.get_system_health()


@router.get("/gateway")
async def get_gateway_status(current_user: str = Depends(get_current_user)):
    """Get Gateway status"""
    collector = StatusCollector()
    return collector.get_gateway_status()


@router.get("/node")
async def get_node_info(current_user: str = Depends(get_current_user)):
    """Get node information"""
    collector = StatusCollector()
    info = collector.get_node_info()

    if not info:
        raise HTTPException(status_code=404, detail="Node info not found")

    return info


@router.get("/logs")
async def get_log_info(current_user: str = Depends(get_current_user)):
    """Get log file information"""
    collector = StatusCollector()
    return collector.get_log_info()


@router.get("/logs/content")
async def get_log_content(current_user: str = Depends(get_current_user), lines: int = 100):
    """Get recent log content"""
    from services.executor import OperationExecutor
    executor = OperationExecutor()
    result = executor.get_recent_logs(lines)

    if not result.success:
        raise HTTPException(status_code=404, detail=result.message)

    return result.data
