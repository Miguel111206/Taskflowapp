from typing import Protocol, Optional
from datetime import datetime, timedelta
import uuid


class IUserRepositoryProtocol(Protocol):
    """Protocol for user repository."""
    
    def create(self, user: "User") -> "User":
        ...
    
    def get_by_id(self, user_id: str) -> Optional["User"]:
        ...
    
    def get_by_username(self, username: str) -> Optional["User"]:
        ...
    
    def get_by_email(self, email: str) -> Optional["User"]:
        ...
    
    def update(self, user: "User") -> "User":
        ...
    
    def delete(self, user_id: str) -> bool:
        ...


class IPasswordHandler(Protocol):
    """Protocol for password handling."""
    
    def hash(self, password: str) -> str:
        ...
    
    def verify(self, password: str, password_hash: str) -> bool:
        ...


class ITokenHandler(Protocol):
    """Protocol for JWT token handling."""
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        ...
    
    def create_refresh_token(self, data: dict) -> str:
        ...
    
    def verify_token(self, token: str) -> dict:
        ...


class User:
    """Domain user entity."""
    
    def __init__(
        self,
        id: Optional[str] = None,
        username: str = "",
        email: str = "",
        password_hash: str = "",
        role: str = "user",
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }