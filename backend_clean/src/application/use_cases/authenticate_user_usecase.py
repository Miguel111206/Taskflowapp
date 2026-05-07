from datetime import timedelta
from typing import Protocol, Optional
from ..dtos.user_dto import LoginDTO
from ..dtos.token_dto import TokenDTO
from ..use_cases.user_entities import User, IUserRepositoryProtocol, IPasswordHandler, ITokenHandler


class AuthenticateUserUseCase:
    """
    Use case for authenticating a user and generating tokens.
    """
    
    def __init__(
        self,
        user_repository: IUserRepositoryProtocol,
        password_handler: IPasswordHandler,
        token_handler: ITokenHandler
    ) -> None:
        self._user_repository = user_repository
        self._password_handler = password_handler
        self._token_handler = token_handler
    
    def execute(self, dto: LoginDTO) -> TokenDTO:
        """Execute authentication."""
        user = self._user_repository.get_by_username(dto.username)
        if not user:
            raise ValueError("Invalid credentials")
        
        if not self._password_handler.verify(dto.password, user.password_hash):
            raise ValueError("Invalid credentials")
        
        if not user.is_active:
            raise ValueError("User account is inactive")
        
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        }
        
        access_token = self._token_handler.create_access_token(
            token_data,
            expires_delta=timedelta(hours=1)
        )
        refresh_token = self._token_handler.create_refresh_token(token_data)
        
        return TokenDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600
        )