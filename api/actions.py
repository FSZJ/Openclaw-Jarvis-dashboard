"""
Actions API routes - operational actions
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth import AuthService
from services.executor import OperationExecutor

router = APIRouter(prefix="/actions", tags=["Actions"])
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


@router.post("/gateway/restart")
async def restart_gateway(current_user: str = Depends(get_current_user)):
    """Restart Gateway"""
    executor = OperationExecutor()
    result = executor.restart_gateway()

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result.dict()


@router.post("/gateway/stop")
async def stop_gateway(current_user: str = Depends(get_current_user)):
    """Stop Gateway"""
    executor = OperationExecutor()
    result = executor.stop_gateway()

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result.dict()


@router.post("/gateway/start")
async def start_gateway(current_user: str = Depends(get_current_user)):
    """Start Gateway"""
    executor = OperationExecutor()
    result = executor.start_gateway()

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result.dict()


@router.post("/backup")
async def create_backup(current_user: str = Depends(get_current_user)):
    """Create a backup"""
    executor = OperationExecutor()
    result = executor.create_backup()

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result.dict()


@router.get("/backups")
async def list_backups(current_user: str = Depends(get_current_user)):
    """List available backups"""
    executor = OperationExecutor()
    result = executor.list_backups()

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result.data


@router.post("/logs/clear")
async def clear_logs(current_user: str = Depends(get_current_user)):
    """Clear log files"""
    executor = OperationExecutor()
    result = executor.clear_logs()

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result.dict()


@router.post("/message/test")
async def send_test_message(current_user: str = Depends(get_current_user)):
    """Send a test message through Gateway"""
    executor = OperationExecutor()
    result = executor.send_message("Test message from OpenClaw Dashboard")

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result.dict()
