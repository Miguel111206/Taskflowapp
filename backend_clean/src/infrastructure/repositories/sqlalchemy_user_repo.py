from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.domain.entities.user import User
from src.domain.repositories.irepositories import IUserRepository
from src.infrastructure.models.user_model import UserModel


class SQLAlchemyUserRepository(IUserRepository):
    """
    SQLAlchemy implementation of IUserRepository.
    """
    
    def __init__(self, session: Session) -> None:
        self._session = session
    
    def _to_entity(self, model: UserModel) -> User:
        """Convert model to entity."""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            role=model.role,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, entity: User) -> UserModel:
        """Convert entity to model."""
        return UserModel(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            password_hash=entity.password_hash,
            role=entity.role,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    def create(self, user: User) -> User:
        """Create a new user."""
        model = self._to_model(user)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        model = self._session.query(UserModel).filter(UserModel.id == user_id).first()
        if model:
            return self._to_entity(model)
        return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        model = self._session.query(UserModel).filter(
            UserModel.username == username
        ).first()
        if model:
            return self._to_entity(model)
        return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        model = self._session.query(UserModel).filter(
            UserModel.email == email
        ).first()
        if model:
            return self._to_entity(model)
        return None
    
    def update(self, user: User) -> User:
        """Update an existing user."""
        model = self._session.query(UserModel).filter(
            UserModel.id == user.id
        ).first()
        if model:
            model.username = user.username
            model.email = user.email
            model.password_hash = user.password_hash
            model.role = user.role
            model.is_active = user.is_active
            model.updated_at = datetime.utcnow()
            self._session.commit()
            self._session.refresh(model)
            return self._to_entity(model)
        return user
    
    def delete(self, user_id: str) -> bool:
        """Delete a user."""
        model = self._session.query(UserModel).filter(
            UserModel.id == user_id
        ).first()
        if model:
            self._session.delete(model)
            self._session.commit()
            return True
        return False
    
    def list_all(self) -> List[User]:
        """List all users."""
        models = self._session.query(UserModel).all()
        return [self._to_entity(m) for m in models]