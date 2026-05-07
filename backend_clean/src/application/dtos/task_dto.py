from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskDTO(BaseModel):
    """
    Data Transfer Object for Task.
    """
    id: str
    title: str
    description: Optional[str] = None
    status: str = "pending"
    owner_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CreateTaskDTO(BaseModel):
    """
    Data Transfer Object for creating a new task.
    """
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Complete project",
                "description": "Finish the backend implementation"
            }
        }


class UpdateTaskDTO(BaseModel):
    """
    Data Transfer Object for updating a task.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern=r'^(pending|in_progress|completed|cancelled)$')
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated title",
                "status": "in_progress"
            }
        }