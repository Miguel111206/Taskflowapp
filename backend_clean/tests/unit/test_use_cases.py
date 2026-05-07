import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.application.use_cases.create_user_usecase import CreateUserUseCase
from src.application.use_cases.authenticate_user_usecase import AuthenticateUserUseCase
from src.application.use_cases.create_task_usecase import CreateTaskUseCase
from src.application.dtos.user_dto import CreateUserDTO, LoginDTO
from src.application.dtos.task_dto import CreateTaskDTO
from src.domain.entities.user import User
from src.domain.entities.task import Task


class MockUserRepository:
    """Mock user repository for testing."""
    
    def __init__(self):
        self.users = {}
        self.created = []
    
    def create(self, user):
        self.users[user.id] = user
        self.created.append(user)
        return user
    
    def get_by_id(self, user_id):
        return self.users.get(user_id)
    
    def get_by_username(self, username):
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def get_by_email(self, email):
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def update(self, user):
        self.users[user.id] = user
        return user
    
    def delete(self, user_id):
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False


class MockTaskRepository:
    """Mock task repository for testing."""
    
    def __init__(self):
        self.tasks = {}
    
    def create(self, task):
        self.tasks[task.id] = task
        return task
    
    def get_by_id(self, task_id):
        return self.tasks.get(task_id)
    
    def update(self, task):
        self.tasks[task.id] = task
        return task
    
    def delete(self, task_id):
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    def list_by_owner(self, owner_id):
        return [
            task for task in self.tasks.values()
            if task.owner_id == owner_id
        ]


class MockPasswordHandler:
    """Mock password handler for testing."""
    
    def hash(self, password):
        return f"hashed_{password}"
    
    def verify(self, password, password_hash):
        return password_hash == f"hashed_{password}"


class MockTokenHandler:
    """Mock token handler for testing."""
    
    def create_access_token(self, data, expires_delta=None):
        return f"access_token_{data.get('sub')}"
    
    def create_refresh_token(self, data):
        return f"refresh_token_{data.get('sub')}"
    
    def verify_token(self, token):
        if "access" in token or "refresh" in token:
            return {"sub": "testuser", "user_id": "123", "role": "user"}
        raise ValueError("Invalid token")


class TestCreateUserUseCase:
    """Tests for CreateUserUseCase."""
    
    def test_create_user_success(self):
        """Test successful user creation."""
        user_repo = MockUserRepository()
        password_handler = MockPasswordHandler()
        
        use_case = CreateUserUseCase(user_repo, password_handler)
        
        dto = CreateUserDTO(
            username="johndoe",
            email="john@example.com",
            password="SecurePass123"
        )
        
        result = use_case.execute(dto)
        
        assert result.username == "johndoe"
        assert result.email == "john@example.com"
    
    def test_create_user_duplicate_username(self):
        """Test duplicate username error."""
        existing_user = User(
            id="existing",
            username="johndoe",
            email="john@example.com",
            password_hash="hashed"
        )
        
        user_repo = MockUserRepository()
        user_repo.users[existing_user.id] = existing_user
        password_handler = MockPasswordHandler()
        
        use_case = CreateUserUseCase(user_repo, password_handler)
        
        dto = CreateUserDTO(
            username="johndoe",
            email="john2@example.com",
            password="SecurePass123"
        )
        
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(dto)
        
        assert "already exists" in str(exc_info.value)
    
    def test_create_user_duplicate_email(self):
        """Test duplicate email error."""
        existing_user = User(
            id="existing",
            username="johndoe",
            email="john@example.com",
            password_hash="hashed"
        )
        
        user_repo = MockUserRepository()
        user_repo.users[existing_user.id] = existing_user
        password_handler = MockPasswordHandler()
        
        use_case = CreateUserUseCase(user_repo, password_handler)
        
        dto = CreateUserDTO(
            username="johndoe2",
            email="john@example.com",
            password="SecurePass123"
        )
        
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(dto)
        
        assert "already exists" in str(exc_info.value)


class TestAuthenticateUserUseCase:
    """Tests for AuthenticateUserUseCase."""
    
    def test_authenticate_success(self):
        """Test successful authentication."""
        user_repo = MockUserRepository()
        user = User(
            id="user-123",
            username="johndoe",
            email="john@example.com",
            password_hash="hashed_SecurePass123",
            is_active=True
        )
        user_repo.users[user.id] = user
        
        password_handler = MockPasswordHandler()
        token_handler = MockTokenHandler()
        
        use_case = AuthenticateUserUseCase(
            user_repo,
            password_handler,
            token_handler
        )
        
        dto = LoginDTO(username="johndoe", password="SecurePass123")
        result = use_case.execute(dto)
        
        assert result.access_token is not None
        assert result.refresh_token is not None
    
    def test_authenticate_invalid_credentials(self):
        """Test invalid credentials error."""
        user_repo = MockUserRepository()
        password_handler = MockPasswordHandler()
        token_handler = MockTokenHandler()
        
        use_case = AuthenticateUserUseCase(
            user_repo,
            password_handler,
            token_handler
        )
        
        dto = LoginDTO(username="johndoe", password="WrongPassword")
        
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(dto)
        
        assert "Invalid credentials" in str(exc_info.value)
    
    def test_authenticate_inactive_user(self):
        """Test inactive user error."""
        user = User(
            id="user-123",
            username="johndoe",
            email="john@example.com",
            password_hash="hashed_SecurePass123",
            is_active=False
        )
        
        user_repo = MockUserRepository()
        user_repo.users[user.id] = user
        password_handler = MockPasswordHandler()
        token_handler = MockTokenHandler()
        
        use_case = AuthenticateUserUseCase(
            user_repo,
            password_handler,
            token_handler
        )
        
        dto = LoginDTO(username="johndoe", password="SecurePass123")
        
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(dto)
        
        assert "inactive" in str(exc_info.value).lower()


class TestCreateTaskUseCase:
    """Tests for CreateTaskUseCase."""
    
    def test_create_task_success(self):
        """Test successful task creation."""
        task_repo = MockTaskRepository()
        use_case = CreateTaskUseCase(task_repo)
        
        dto = CreateTaskDTO(
            title="My Task",
            description="Task description"
        )
        
        result = use_case.execute(dto, "user-123")
        
        assert result.title == "My Task"
        assert result.description == "Task description"
        assert result.status == "pending"
        assert result.owner_id == "user-123"