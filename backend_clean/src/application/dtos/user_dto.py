from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserDTO(BaseModel):
    """
    Data Transfer Object for User.
    """
    id: str
    username: str
    email: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CreateUserDTO(BaseModel):
    """
    Data Transfer Object for creating a new user.
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=8)
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePass123"
            }
        }


class UpdateUserDTO(BaseModel):
    """
    Data Transfer Object for updating a user.
    """
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    role: Optional[str] = Field(None, pattern=r'^(user|admin)$')
    is_active: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe_updated",
                "role": "admin"
            }
        }


class LoginDTO(BaseModel):
    """
    Data Transfer Object for user login.
    """
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    
    class Config:
        json_schema_extra = {
            "username": "johndoe",
            "password": "SecurePass123"
        }