"""
Tasks/Todos API routes - todo and task management
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth import AuthService
from services.collector import StatusCollector
from services.task_store import TaskStore
from models import TodoCreateRequest

router = APIRouter(prefix="/tasks", tags=["Tasks"])
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


@router.get("/todos")
async def get_todos(current_user: str = Depends(get_current_user)):
    """Get pending todos from local store."""
    collector = StatusCollector()
    return {"todos": collector.get_todos()}


@router.get("/completed")
async def get_completed_tasks(current_user: str = Depends(get_current_user)):
    """Get completed tasks from local store."""
    collector = StatusCollector()
    return {"tasks": collector.get_completed_tasks()}


@router.get("/history")
async def get_history_tasks(current_user: str = Depends(get_current_user)):
    """Alias for completed tasks (history)."""
    collector = StatusCollector()
    return collector.get_completed_tasks()


@router.post("/sync")
async def sync_with_apple(current_user: str = Depends(get_current_user)):
    """Apple reminders sync has been disabled."""
    StatusCollector.invalidate_todos_cache()
    return {
        "success": False,
        "message": "Apple 提醒同步功能已停用，当前仅使用本地任务。",
        "synced": {"todos": 0, "history": 0, "apple_available": False},
        "todos": TaskStore.list_todos(),
        "history": TaskStore.list_completed(limit=30),
    }


@router.post("/todos")
async def create_todo(payload: TodoCreateRequest, current_user: str = Depends(get_current_user)):
    """Create todo item in local store."""
    try:
        local_created = TaskStore.create_todo(
            title=payload.title,
            list_name=payload.list_name or "默认列表",
            due_date=payload.due_date
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    StatusCollector.invalidate_todos_cache()
    return {
        "success": True,
        "message": "任务已创建",
        "data": local_created,
        "todos": TaskStore.list_todos()
    }


@router.post("/todos/{task_id}/complete")
async def complete_todo(task_id: str, current_user: str = Depends(get_current_user)):
    """Complete local task."""
    task = TaskStore.complete_todo(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    StatusCollector.invalidate_todos_cache()
    return {
        "success": True,
        "message": "任务已完成",
        "todos": TaskStore.list_todos(),
        "history": TaskStore.list_completed(limit=30),
    }


@router.post("/history/{task_id}/reopen")
async def reopen_task(task_id: str, current_user: str = Depends(get_current_user)):
    """Reopen local completed task."""
    task = TaskStore.reopen_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="历史任务不存在")
    StatusCollector.invalidate_todos_cache()
    return {
        "success": True,
        "message": "任务已恢复",
        "todos": TaskStore.list_todos(),
        "history": TaskStore.list_completed(limit=30),
    }
