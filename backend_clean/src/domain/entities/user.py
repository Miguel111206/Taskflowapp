from datetime import datetime
from typing import Optional, Any
from .base import BaseEntity


class User(BaseEntity):
    """
    User entity representing a system user with authentication and authorization.
    Inherits from BaseEntity and encapsulates password hashing.
    """
    
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
        super().__init__(id, created_at, updated_at)
        self._username = username
        self._email = email
        self._password_hash = password_hash
        self._role = role
        self._is_active = is_active
    
    @property
    def username(self) -> str:
        """Username of the user."""
        return self._username
    
    @username.setter
    def username(self, value: str) -> None:
        """Set username with validation."""
        if not value or len(value) < 3:
            raise ValueError("Username must be at least 3 characters")
        self._username = value
        self.update_timestamp()
    
    @property
    def email(self) -> str:
        """Email address of the user."""
        return self._email
    
    @email.setter
    def email(self, value: str) -> None:
        """Set email with basic validation."""
        if value and "@" not in value:
            raise ValueError("Invalid email format")
        self._email = value
        self.update_timestamp()
    
    @property
    def password_hash(self) -> str:
        """
        Encapsulated password hash - read-only from outside.
        Returns the hash for verification but never exposes raw password.
        """
        return self._password_hash
    
    def set_password(self, password_hash: str) -> None:
        """Set password hash internally."""
        self._password_hash = password_hash
        self.update_timestamp()
    
    @property
    def role(self) -> str:
        """User role for authorization (user, admin)."""
        return self._role
    
    @role.setter
    def role(self, value: str) -> None:
        """Set user role with validation."""
        if value not in ["user", "admin"]:
            raise ValueError("Role must be 'user' or 'admin'")
        self._role = value
        self.update_timestamp()
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self._role == "admin"
    
    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self._is_active
    
    @is_active.setter
    def is_active(self, value: bool) -> None:
        """Set active status."""
        self._is_active = value
        self.update_timestamp()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert user to dictionary (excludes password hash)."""
        return {
            "id": self._id,
            "username": self._username,
            "email": self._email,
            "role": self._role,
            "is_active": self._is_active,
            "created_at": self._created_at.isoformat() if self._created_at else None,
            "updated_at": self._updated_at.isoformat() if self._updated_at else None
        }
    
    def verify_password(self, password_hash: str) -> bool:
        """Verify if provided hash matches stored hash."""
        return self._password_hash == password_hash