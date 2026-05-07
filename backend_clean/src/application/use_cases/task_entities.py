from typing import Protocol, Optional
from datetime import datetime
import uuid


class Task:
    """Domain task entity."""
    
    VALID_STATUSES = ["pending", "in_progress", "completed", "cancelled"]
    
    def __init__(
        self,
        id: Optional[str] = None,
        title: str = "",
        description: str = "",
        status: str = "pending",
        owner_id: str = "",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.status = self._validate_status(status)
        self.owner_id = owner_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def _validate_status(self, status: str) -> str:
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(self.VALID_STATUSES)}")
        return status
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ITaskRepositoryProtocol(Protocol):
    """Protocol for task repository."""
    
    def create(self, task: Task) -> Task:
        ...
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        ...
    
    def update(self, task: Task) -> Task:
        ...
    
    def delete(self, task_id: str) -> bool:
        ...
    
    def list_by_owner(self, owner_id: str) -> list[Task]:
        ...
    
    def list_all(self) -> list[Task]:
        ...