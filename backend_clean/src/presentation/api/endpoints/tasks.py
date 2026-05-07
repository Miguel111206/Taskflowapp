from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.application.dtos.task_dto import CreateTaskDTO, UpdateTaskDTO, TaskDTO
from src.application.dtos.response_dto import ResponseDTO
from src.application.use_cases.create_task_usecase import CreateTaskUseCase
from src.application.use_cases.update_task_usecase import UpdateTaskUseCase
from src.application.use_cases.delete_task_usecase import DeleteTaskUseCase
from src.application.use_cases.list_tasks_usecase import ListTasksUseCase
from src.application.use_cases.get_task_usecase import GetTaskUseCase
from src.application.use_cases.complete_task_usecase import CompleteTaskUseCase
from src.infrastructure.database.session import get_session
from src.infrastructure.repositories.sqlalchemy_task_repo import SQLAlchemyTaskRepository
from src.domain.entities.user import User
from src.presentation.dependencies.injection import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])

get_db = get_session


def get_task_repository(session: Session = Depends(get_db)):
    return SQLAlchemyTaskRepository(session)


@router.post("/", response_model=TaskDTO, status_code=status.HTTP_201_CREATED)
async def create_task(
    dto: CreateTaskDTO,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Create a new task."""
    task_repo = SQLAlchemyTaskRepository(session)
    use_case = CreateTaskUseCase(task_repo)
    
    task_dto = use_case.execute(dto, current_user.id)
    return task_dto


@router.get("/", response_model=List[TaskDTO])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """List all tasks for current user."""
    task_repo = SQLAlchemyTaskRepository(session)
    use_case = ListTasksUseCase(task_repo)
    
    tasks = use_case.execute(current_user.id)
    return tasks


@router.get("/{task_id}", response_model=TaskDTO)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Get a single task."""
    task_repo = SQLAlchemyTaskRepository(session)
    use_case = GetTaskUseCase(task_repo)
    
    try:
        task = use_case.execute(task_id, current_user.id)
        return task
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{task_id}", response_model=TaskDTO)
async def update_task(
    task_id: str,
    dto: UpdateTaskDTO,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Update a task."""
    task_repo = SQLAlchemyTaskRepository(session)
    use_case = UpdateTaskUseCase(task_repo)
    
    try:
        task = use_case.execute(task_id, dto, current_user.id)
        return task
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Delete a task."""
    task_repo = SQLAlchemyTaskRepository(session)
    use_case = DeleteTaskUseCase(task_repo)
    
    try:
        use_case.execute(task_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{task_id}/complete", response_model=TaskDTO)
async def complete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Mark a task as completed."""
    task_repo = SQLAlchemyTaskRepository(session)
    use_case = CompleteTaskUseCase(task_repo)
    
    try:
        task = use_case.execute(task_id, current_user.id)
        return task
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )