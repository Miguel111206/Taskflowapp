from typing import Protocol, Callable, Optional
from datetime import datetime, timedelta
from ..dtos.user_dto import CreateUserDTO, UserDTO
from ..use_cases.user_entities import User, IUserRepositoryProtocol, IPasswordHandler, ITokenHandler


class CreateUserUseCase:
    """
    Use case for creating a new user.
    """
    
    def __init__(
        self,
        user_repository: IUserRepositoryProtocol,
        password_handler: IPasswordHandler
    ) -> None:
        self._user_repository = user_repository
        self._password_handler = password_handler
    
    def execute(self, dto: CreateUserDTO) -> UserDTO:
        """Execute the use case."""
        existing_user = self._user_repository.get_by_username(dto.username)
        if existing_user:
            raise ValueError(f"Username {dto.username} already exists")
        
        existing_email = self._user_repository.get_by_email(dto.email)
        if existing_email:
            raise ValueError(f"Email {dto.email} already exists")
        
        password_hash = self._password_handler.hash(dto.password)
        
        user = User(
            username=dto.username,
            email=dto.email,
            password_hash=password_hash,
            role="user",
            is_active=True
        )
        
        created_user = self._user_repository.create(user)
        
        return UserDTO(
            id=created_user.id,
            username=created_user.username,
            email=created_user.email,
            role=created_user.role,
            is_active=created_user.is_active,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at
        )