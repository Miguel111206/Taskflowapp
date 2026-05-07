from typing import Protocol, Optional
from ..dtos.task_dto import UpdateTaskDTO, TaskDTO
from ..use_cases.task_entities import Task, ITaskRepositoryProtocol


class UpdateTaskUseCase:
    """
    Use case for updating an existing task.
    """
    
    def __init__(
        self,
        task_repository: ITaskRepositoryProtocol
    ) -> None:
        self._task_repository = task_repository
    
    def execute(self, task_id: str, dto: UpdateTaskDTO, user_id: str) -> TaskDTO:
        """Execute the use case."""
        task = self._task_repository.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task.owner_id != user_id:
            raise ValueError("Not authorized to update this task")
        
        if dto.title is not None:
            task.title = dto.title
        if dto.description is not None:
            task.description = dto.description
        if dto.status is not None:
            task.status = task._validate_status(dto.status)
        
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