from enum import Enum


class TaskStatus(str, Enum):
    """
    Value object representing task status.
    """
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
    @classmethod
    def values(cls) -> list[str]:
        """Get all valid status values."""
        return [status.value for status in cls]
    
    def __str__(self) -> str:
        return self.value