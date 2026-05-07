from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
import uuid


class BaseEntity(ABC):
    """
    Abstract base entity providing common attributes and behavior
    for all domain entities. Implements core entity functionality.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> None:
        self._id = id or str(uuid.uuid4())
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or datetime.utcnow()
    
    @property
    def id(self) -> str:
        """Unique identifier for the entity."""
        return self._id
    
    @property
    def created_at(self) -> datetime:
        """Timestamp when the entity was created."""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """Timestamp when the entity was last updated."""
        return self._updated_at
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self._updated_at = datetime.utcnow()
    
    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert entity to dictionary representation."""
        pass
    
    def __eq__(self, other: Any) -> bool:
        """Check equality based on entity ID."""
        if not isinstance(other, BaseEntity):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """Hash based on entity ID."""
        return hash(self._id)
    
    def __repr__(self) -> str:
        """String representation of the entity."""
        return f"{self.__class__.__name__}(id={self._id})"