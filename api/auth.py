"""
Authentication API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models import UserLogin, TokenResponse, UserResponse, PasswordChange
from services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    auth_service = AuthService()
    username = auth_service.verify_token(token)

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return username


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login and get access token"""
    auth_service = AuthService()

    user = auth_service.authenticate(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    token = auth_service.create_token(user["username"])

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            username=user["username"],
            must_change_password=user["must_change_password"]
        )
    )


@router.post("/change-password", response_model=dict)
async def change_password(data: PasswordChange, current_user: str = Depends(get_current_user)):
    """Change password"""
    auth_service = AuthService()

    success = auth_service.change_password(
        current_user,
        data.old_password,
        data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password"
        )

    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: str = Depends(get_current_user)):
    """Get current user info"""
    auth_service = AuthService()
    users = auth_service.list_users()

    for user in users:
        if user["username"] == current_user:
            return UserResponse(
                username=user["username"],
                must_change_password=user["must_change_password"]
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.get("/users", response_model=list)
async def list_users(current_user: str = Depends(get_current_user)):
    """List all users (admin only)"""
    auth_service = AuthService()
    return auth_service.list_users()
