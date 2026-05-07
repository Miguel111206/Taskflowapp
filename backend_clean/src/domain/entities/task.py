from datetime import datetime
from typing import Optional, Any
from .base import BaseEntity


class Task(BaseEntity):
    """
    Task entity representing a task item owned by a user.
    Inherits from BaseEntity and encapsulates ownership.
    """
    
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
        super().__init__(id, created_at, updated_at)
        self._title = title
        self._description = description
        self._status = self._validate_status(status)
        self._owner_id = owner_id
    
    @property
    def title(self) -> str:
        """Title of the task."""
        return self._title
    
    @title.setter
    def title(self, value: str) -> None:
        """Set title with validation."""
        if not value or len(value) < 1:
            raise ValueError("Title cannot be empty")
        self._title = value
        self.update_timestamp()
    
    @property
    def description(self) -> str:
        """Description of the task."""
        return self._description
    
    @description.setter
    def description(self, value: str) -> None:
        """Set description."""
        self._description = value
        self.update_timestamp()
    
    @property
    def status(self) -> str:
        """
        Status of the task with validation.
        Validates that status is one of: pending, in_progress, completed, cancelled
        """
        return self._status
    
    @status.setter
    def status(self, value: str) -> None:
        """Set status with validation."""
        self._status = self._validate_status(value)
        self.update_timestamp()
    
    def _validate_status(self, status: str) -> str:
        """Validate task status."""
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(self.VALID_STATUSES)}")
        return status
    
    @property
    def owner_id(self) -> str:
        """
        Encapsulated owner_id - owner of the task.
        """
        return self._owner_id
    
    @owner_id.setter
    def owner_id(self, value: str) -> None:
        """Set owner_id."""
        if not value:
            raise ValueError("Owner ID cannot be empty")
        self._owner_id = value
        self.update_timestamp()
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self._status == "completed"
    
    def complete(self) -> None:
        """Mark task as completed."""
        self._status = "completed"
        self.update_timestamp()
    
    def cancel(self) -> None:
        """Mark task as cancelled."""
        self._status = "cancelled"
        self.update_timestamp()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self._id,
            "title": self._title,
            "description": self._description,
            "status": self._status,
            "owner_id": self._owner_id,
            "created_at": self._created_at.isoformat() if self._created_at else None,
            "updated_at": self._updated_at.isoformat() if self._updated_at else None
        }