from pydantic import BaseModel, Field
from typing import Optional


class TokenDTO(BaseModel):
    """
    Data Transfer Object for authentication tokens.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class RefreshTokenDTO(BaseModel):
    """
    Data Transfer Object for refreshing tokens.
    """
    refresh_token: str = Field(...)
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }