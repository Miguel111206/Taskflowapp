from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.application.dtos.user_dto import CreateUserDTO, LoginDTO, UserDTO
from src.application.dtos.token_dto import TokenDTO, RefreshTokenDTO
from src.application.dtos.response_dto import ResponseDTO
from src.application.use_cases.create_user_usecase import CreateUserUseCase
from src.application.use_cases.authenticate_user_usecase import AuthenticateUserUseCase
from src.infrastructure.database.session import get_session
from src.infrastructure.repositories.sqlalchemy_user_repo import SQLAlchemyUserRepository
from src.infrastructure.auth.jwt_handler import JWTHandler
from src.infrastructure.auth.password_handler import PasswordHandler
from src.domain.entities.user import User
from src.presentation.dependencies.injection import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

get_db = get_session


def get_user_repository(session: Session = Depends(get_db)):
    return SQLAlchemyUserRepository(session)


@router.post("/register", response_model=ResponseDTO, status_code=status.HTTP_201_CREATED)
async def register(
    dto: CreateUserDTO,
    session: Session = Depends(get_db)
):
    """Register a new user."""
    user_repo = SQLAlchemyUserRepository(session)
    password_handler = PasswordHandler()
    
    use_case = CreateUserUseCase(user_repo, password_handler)
    
    try:
        user_dto = use_case.execute(dto)
        return ResponseDTO(
            success=True,
            message="User created successfully",
            data=user_dto.model_dump()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenDTO)
async def login(
    dto: LoginDTO,
    session: Session = Depends(get_db)
):
    """Login and get access tokens."""
    user_repo = SQLAlchemyUserRepository(session)
    password_handler = PasswordHandler()
    jwt_handler = JWTHandler()
    
    use_case = AuthenticateUserUseCase(
        user_repo,
        password_handler,
        jwt_handler
    )
    
    try:
        token_dto = use_case.execute(dto)
        return token_dto
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenDTO)
async def refresh_token(
    dto: RefreshTokenDTO,
    session: Session = Depends(get_db)
):
    """Refresh access token."""
    jwt_handler = JWTHandler()
    
    try:
        payload = jwt_handler.verify_token(dto.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        token_data = {
            "sub": payload.get("sub"),
            "user_id": payload.get("user_id"),
            "role": payload.get("role")
        }
        
        new_access_token = jwt_handler.create_access_token(token_data)
        new_refresh_token = jwt_handler.create_refresh_token(token_data)
        
        return TokenDTO(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=3600
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserDTO)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get current user info."""
    return UserDTO(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )