from typing import Protocol, List
from ..dtos.task_dto import CreateTaskDTO, TaskDTO
from ..use_cases.task_entities import Task, ITaskRepositoryProtocol


class CreateTaskUseCase:
    """
    Use case for creating a new task.
    """
    
    def __init__(
        self,
        task_repository: ITaskRepositoryProtocol
    ) -> None:
        self._task_repository = task_repository
    
    def execute(self, dto: CreateTaskDTO, owner_id: str) -> TaskDTO:
        """Execute the use case."""
        task = Task(
            title=dto.title,
            description=dto.description or "",
            status="pending",
            owner_id=owner_id
        )
        
        created_task = self._task_repository.create(task)
        
        return TaskDTO(
            id=created_task.id,
            title=created_task.title,
            description=created_task.description,
            status=created_task.status,
            owner_id=created_task.owner_id,
            created_at=created_task.created_at,
            updated_at=created_task.updated_at
        )