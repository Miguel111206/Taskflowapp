from typing import Protocol, Optional
from ..dtos.task_dto import TaskDTO
from ..use_cases.task_entities import ITaskRepositoryProtocol


class GetTaskUseCase:
    """
    Use case for getting a single task.
    """
    
    def __init__(
        self,
        task_repository: ITaskRepositoryProtocol
    ) -> None:
        self._task_repository = task_repository
    
    def execute(self, task_id: str, user_id: str) -> Optional[TaskDTO]:
        """Execute the use case."""
        task = self._task_repository.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task.owner_id != user_id:
            raise ValueError("Not authorized to access this task")
        
        return TaskDTO(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            owner_id=task.owner_id,
            created_at=task.created_at,
            updated_at=task.updated_at
        )