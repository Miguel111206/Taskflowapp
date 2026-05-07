from typing import Protocol
from ..dtos.task_dto import TaskDTO
from ..use_cases.task_entities import ITaskRepositoryProtocol


class CompleteTaskUseCase:
    """
    Use case for completing a task.
    """
    
    def __init__(
        self,
        task_repository: ITaskRepositoryProtocol
    ) -> None:
        self._task_repository = task_repository
    
    def execute(self, task_id: str, user_id: str) -> TaskDTO:
        """Execute the use case."""
        task = self._task_repository.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task.owner_id != user_id:
            raise ValueError("Not authorized to complete this task")
        
        task.status = "completed"
        
        updated_task = self._task_repository.update(task)
        
        return TaskDTO(
            id=updated_task.id,
            title=updated_task.title,
            description=updated_task.description,
            status=updated_task.status,
            owner_id=updated_task.owner_id,
            created_at=updated_task.created_at,
            updated_at=updated_task.updated_at
        )