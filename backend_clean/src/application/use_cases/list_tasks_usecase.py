from typing import Protocol, List
from ..dtos.task_dto import TaskDTO
from ..use_cases.task_entities import ITaskRepositoryProtocol


class ListTasksUseCase:
    """
    Use case for listing tasks.
    """
    
    def __init__(
        self,
        task_repository: ITaskRepositoryProtocol
    ) -> None:
        self._task_repository = task_repository
    
    def execute(self, owner_id: str) -> List[TaskDTO]:
        """Execute the use case."""
        tasks = self._task_repository.list_by_owner(owner_id)
        
        return [
            TaskDTO(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                owner_id=task.owner_id,
                created_at=task.created_at,
                updated_at=task.updated_at
            )
            for task in tasks
        ]