# Asignado: Copilot — estado: done
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    is_admin: bool = Field(default=False)
    role: str = Field(default="user")
    is_2fa_enabled: bool = Field(default=False)
    totp_secret: Optional[str] = Field(default=None)
    login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)

class Task(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    status: str = "todo"
    owner: Optional[str] = Field(default=None, index=True)
    image: Optional[str] = Field(default=None, nullable=True)
    priority: str = Field(default="media")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
