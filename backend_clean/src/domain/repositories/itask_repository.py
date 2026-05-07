from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.task import Task


class ITaskRepository(ABC):
    """
    Abstract repository interface for Task entity.
    Defines the contract for task persistence operations.
    """
    
    @abstractmethod
    def create(self, task: Task) -> Task:
        """
        Create a new task.
        
        Args:
            task: Task entity to create
            
        Returns:
            Created task with generated ID
        """
        pass
    
    @abstractmethod
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update(self, task: Task) -> Task:
        """
        Update an existing task.
        
        Args:
            task: Task entity to update
            
        Returns:
            Updated task
        """
        pass
    
    @abstractmethod
    def delete(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def list_by_owner(self, owner_id: str) -> List[Task]:
        """
        List all tasks for a specific owner.
        
        Args:
            owner_id: Owner identifier
            
        Returns:
            List of tasks owned by the user
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[Task]:
        """
        List all tasks.
        
        Returns:
            List of all tasks
        """
        pass
    
    @abstractmethod
    def get_by_status(self, status: str) -> List[Task]:
        """
        Get tasks by status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of tasks with specified status
        """
        pass