from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.domain.entities.task import Task
from src.domain.repositories.itask_repository import ITaskRepository
from src.infrastructure.models.task_model import TaskModel


class SQLAlchemyTaskRepository(ITaskRepository):
    """SQLAlchemy implementation of ITaskRepository."""

    def __init__(self, session: Session) -> None:
        self._session = session
    
    def _to_entity(self, model: TaskModel) -> Task:
        """Convert model to entity."""
        return Task(
            id=model.id,
            title=model.title,
            description=model.description,
            status=model.status,
            owner_id=model.owner_id,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, entity: Task) -> TaskModel:
        """Convert entity to model."""
        return TaskModel(
            id=entity.id,
            title=entity.title,
            description=entity.description,
            status=entity.status,
            owner_id=entity.owner_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    def create(self, task: Task) -> Task:
        """Create a new task."""
        model = self._to_model(task)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        model = self._session.query(TaskModel).filter(TaskModel.id == task_id).first()
        if model:
            return self._to_entity(model)
        return None
    
    def update(self, task: Task) -> Task:
        """Update an existing task."""
        model = self._session.query(TaskModel).filter(
            TaskModel.id == task.id
        ).first()
        if model:
            model.title = task.title
            model.description = task.description
            model.status = task.status
            model.updated_at = datetime.utcnow()
            self._session.commit()
            self._session.refresh(model)
            return self._to_entity(model)
        return task
    
    def delete(self, task_id: str) -> bool:
        """Delete a task."""
        model = self._session.query(TaskModel).filter(
            TaskModel.id == task_id
        ).first()
        if model:
            self._session.delete(model)
            self._session.commit()
            return True
        return False
    
    def list_by_owner(self, owner_id: str) -> List[Task]:
        """List all tasks for a specific owner."""
        models = self._session.query(TaskModel).filter(
            TaskModel.owner_id == owner_id
        ).all()
        return [self._to_entity(m) for m in models]
    
    def list_all(self) -> List[Task]:
        """List all tasks."""
        models = self._session.query(TaskModel).all()
        return [self._to_entity(m) for m in models]
    
    def get_by_status(self, status: str) -> List[Task]:
        """Get tasks by status."""
        models = self._session.query(TaskModel).filter(
            TaskModel.status == status
        ).all()
        return [self._to_entity(m) for m in models]