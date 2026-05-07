from typing import Protocol
from ..use_cases.task_entities import ITaskRepositoryProtocol


class DeleteTaskUseCase:
    """
    Use case for deleting a task.
    """
    
    def __init__(
        self,
        task_repository: ITaskRepositoryProtocol
    ) -> None:
        self._task_repository = task_repository
    
    def execute(self, task_id: str, user_id: str) -> bool:
        """Execute the use case."""
        task = self._task_repository.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task.owner_id != user_id:
            raise ValueError("Not authorized to delete this task")
        
        return self._task_repository.delete(task_id)