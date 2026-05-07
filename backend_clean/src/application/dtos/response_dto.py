from pydantic import BaseModel, Field
from typing import Optional


class ResponseDTO(BaseModel):
    """
    Generic response wrapper.
    """
    success: bool
    message: str
    data: Optional[dict] = None


class ErrorResponseDTO(BaseModel):
    """
    Error response DTO.
    """
    error: str
    detail: Optional[str] = None