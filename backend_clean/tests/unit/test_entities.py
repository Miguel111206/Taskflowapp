import pytest
from datetime import datetime
from src.domain.entities.base import BaseEntity
from src.domain.entities.user import User
from src.domain.entities.task import Task


class TestBaseEntity:
    """Tests for BaseEntity."""
    
    def test_base_entity_creation(self):
        """Test base entity is created with generated ID."""
        class ConcreteEntity(BaseEntity):
            def to_dict(self):
                return {"id": self.id}
        
        entity = ConcreteEntity()
        assert entity.id is not None
        assert len(entity.id) > 0
        assert entity.created_at is not None
        assert entity.updated_at is not None
    
    def test_base_entity_custom_id(self):
        """Test base entity with custom ID."""
        class ConcreteEntity(BaseEntity):
            def to_dict(self):
                return {"id": self.id}
        
        entity = ConcreteEntity(id="custom-id")
        assert entity.id == "custom-id"
    
    def test_update_timestamp(self):
        """Test timestamp update."""
        class ConcreteEntity(BaseEntity):
            def to_dict(self):
                return {"id": self.id}
        
        entity = ConcreteEntity()
        original_updated_at = entity.updated_at
        
        import time
        time.sleep(0.01)
        entity.update_timestamp()
        
        assert entity.updated_at > original_updated_at
    
    def test_equality(self):
        """Test entity equality."""
        class ConcreteEntity(BaseEntity):
            def to_dict(self):
                return {"id": self.id}
        
        entity1 = ConcreteEntity(id="test-id")
        entity2 = ConcreteEntity(id="test-id")
        entity3 = ConcreteEntity(id="other-id")
        
        assert entity1 == entity2
        assert entity1 != entity3
        assert entity1 != "not-an-entity"


class TestUserEntity:
    """Tests for User entity."""
    
    def test_user_creation(self):
        """Test user entity creation."""
        user = User(
            username="johndoe",
            email="john@example.com",
            password_hash="hashed_password",
            role="user"
        )
        
        assert user.username == "johndoe"
        assert user.email == "john@example.com"
        assert user.password_hash == "hashed_password"
        assert user.role == "user"
        assert user.is_active is True
    
    def test_user_username_validation(self):
        """Test username validation."""
        user = User(username="johndoe", email="john@example.com")
        
        with pytest.raises(ValueError):
            user.username = "ab"
        
        with pytest.raises(ValueError):
            user.username = ""
    
    def test_user_role_validation(self):
        """Test role validation."""
        user = User(username="johndoe", email="john@example.com")
        
        with pytest.raises(ValueError):
            user.role = "superadmin"
    
    def test_user_is_admin(self):
        """Test is_admin property."""
        regular_user = User(username="user", email="user@test.com", role="user")
        admin_user = User(username="admin", email="admin@test.com", role="admin")
        
        assert regular_user.is_admin is False
        assert admin_user.is_admin is True
    
    def test_user_password_encapsulation(self):
        """Test password hash encapsulation."""
        user = User(
            username="johndoe",
            email="john@example.com",
            password_hash="secret_hash"
        )
        
        assert user.password_hash == "secret_hash"
        
        user.set_password("new_hash")
        assert user.password_hash == "new_hash"
    
    def test_user_to_dict(self):
        """Test user to_dict method."""
        user = User(
            id="user-123",
            username="johndoe",
            email="john@example.com",
            role="user"
        )
        
        user_dict = user.to_dict()
        
        assert user_dict["id"] == "user-123"
        assert user_dict["username"] == "johndoe"
        assert user_dict["email"] == "john@example.com"
        assert user_dict["role"] == "user"
        assert "password_hash" not in user_dict


class TestTaskEntity:
    """Tests for Task entity."""
    
    def test_task_creation(self):
        """Test task entity creation."""
        task = Task(
            title="My Task",
            description="Task description",
            status="pending",
            owner_id="user-123"
        )
        
        assert task.title == "My Task"
        assert task.description == "Task description"
        assert task.status == "pending"
        assert task.owner_id == "user-123"
    
    def test_task_status_validation(self):
        """Test status validation."""
        task = Task(title="Task", owner_id="user-123")
        
        for valid_status in ["pending", "in_progress", "completed", "cancelled"]:
            task.status = valid_status
            assert task.status == valid_status
        
        with pytest.raises(ValueError):
            task.status = "invalid"
    
    def test_task_title_validation(self):
        """Test title validation."""
        task = Task(title="Task", owner_id="user-123")
        
        with pytest.raises(ValueError):
            task.title = ""
    
    def test_task_owner_encapsulation(self):
        """Test owner encapsulation."""
        task = Task(title="Task", owner_id="user-123")
        
        assert task.owner_id == "user-123"
        
        task.owner_id = "user-456"
        assert task.owner_id == "user-456"
    
    def test_task_complete(self):
        """Test task completion."""
        task = Task(title="Task", owner_id="user-123")
        
        assert task.is_completed is False
        task.complete()
        assert task.is_completed is True
        assert task.status == "completed"
    
    def test_task_cancel(self):
        """Test task cancellation."""
        task = Task(title="Task", owner_id="user-123")
        
        task.cancel()
        assert task.status == "cancelled"
    
    def test_task_to_dict(self):
        """Test task to_dict method."""
        task = Task(
            id="task-123",
            title="My Task",
            description="Description",
            status="pending",
            owner_id="user-123"
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["id"] == "task-123"
        assert task_dict["title"] == "My Task"
        assert task_dict["description"] == "Description"
        assert task_dict["status"] == "pending"
        assert task_dict["owner_id"] == "user-123"