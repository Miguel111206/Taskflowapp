from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.infrastructure.database.session import get_session
from src.infrastructure.repositories.sqlalchemy_user_repo import SQLAlchemyUserRepository
from src.domain.entities.user import User
from src.infrastructure.auth.jwt_handler import JWTHandler

security = HTTPBearer()
jwt_handler = JWTHandler()


def get_db() -> Session:
    """Get database session."""
    generator = get_session()
    return next(generator)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    """
    try:
        token = credentials.credentials
        payload = jwt_handler.verify_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user_repo = SQLAlchemyUserRepository(session)
    user = user_repo.get_by_username(username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user