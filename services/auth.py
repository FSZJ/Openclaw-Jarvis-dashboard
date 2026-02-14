"""
Authentication service for OpenClaw Dashboard
"""
import json
import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from config import (
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES,
    PASSWORDS_FILE, DEFAULT_ADMIN, OPENCLAW_DIR
)
from models import UserCreate, UserResponse


class AuthService:
    """Handles user authentication and management"""

    def __init__(self):
        self._ensure_users_file()

    def _ensure_users_file(self):
        """Create users file if it doesn't exist"""
        if not PASSWORDS_FILE.exists():
            # Create with default admin user
            users = {
                DEFAULT_ADMIN["username"]: {
                    "password": self._hash_password(DEFAULT_ADMIN["password"]),
                    "must_change_password": True,
                    "created_at": datetime.now().isoformat()
                }
            }
            PASSWORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PASSWORDS_FILE, 'w') as f:
                json.dump(users, f, indent=2)

    def _hash_password(self, password: str) -> str:
        """Hash a password"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against a hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def _load_users(self) -> Dict[str, Any]:
        """Load users from file"""
        if not PASSWORDS_FILE.exists():
            self._ensure_users_file()

        with open(PASSWORDS_FILE) as f:
            return json.load(f)

    def _save_users(self, users: Dict[str, Any]):
        """Save users to file"""
        with open(PASSWORDS_FILE, 'w') as f:
            json.dump(users, f, indent=2)

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user and return user info if successful"""
        users = self._load_users()

        if username not in users:
            return None

        user_data = users[username]
        if not self._verify_password(password, user_data["password"]):
            return None

        return {
            "username": username,
            "must_change_password": user_data.get("must_change_password", False)
        }

    def create_token(self, username: str) -> str:
        """Create a JWT token for a user"""
        payload = {
            "sub": username,
            "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def verify_token(self, token: str) -> Optional[str]:
        """Verify a JWT token and return username"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload.get("sub")
        except JWTError:
            return None

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change a user's password"""
        users = self._load_users()

        if username not in users:
            return False

        user_data = users[username]

        if not self._verify_password(old_password, user_data["password"]):
            return False

        user_data["password"] = self._hash_password(new_password)
        user_data["must_change_password"] = False
        user_data["password_changed_at"] = datetime.now().isoformat()

        self._save_users(users)
        return True

    def create_user(self, username: str, password: str) -> bool:
        """Create a new user"""
        users = self._load_users()

        if username in users:
            return False

        users[username] = {
            "password": self._hash_password(password),
            "must_change_password": False,
            "created_at": datetime.now().isoformat()
        }

        self._save_users(users)
        return True

    def delete_user(self, username: str) -> bool:
        """Delete a user (cannot delete admin)"""
        if username == "admin":
            return False

        users = self._load_users()

        if username not in users:
            return False

        del users[username]
        self._save_users(users)
        return True

    def list_users(self) -> list:
        """List all users (without passwords)"""
        users = self._load_users()

        return [
            {
                "username": username,
                "must_change_password": data.get("must_change_password", False),
                "created_at": data.get("created_at")
            }
            for username, data in users.items()
        ]
