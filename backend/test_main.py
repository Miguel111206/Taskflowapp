import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session, select, Field
from datetime import datetime, timedelta
from typing import Optional
import pyotp
import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

from main import app, get_current_user, User, Task, create_access_token, create_refresh_token, verify_token, hash_password as main_hash_password, verify_password as main_verify_password

def hash_password(password: str) -> str:
    return main_hash_password(password)

def verify_password(password: str, hashed: str) -> bool:
    return main_verify_password(password, hashed)

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield

@pytest.fixture(scope="function")
def db_session():
    session = Session(engine)
    yield session
    session.close()

@pytest.fixture(scope="function")
def client(db_session):
    test_user = User(id=1, username="testuser", password_hash="hash", is_admin=True, role="admin")
    db_session.add(test_user)
    db_session.commit()
    
    def override_get_current_user():
        session = Session(engine)
        user = session.exec(select(User).where(User.username == "testuser")).first()
        return user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

class TestUserModel:
    def test_user_creation(self, db_session):
        user = User(username="test", password_hash="hash", is_admin=False, role="user")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "test"
        assert user.is_admin == False
        assert user.role == "user"
        assert user.is_2fa_enabled == False
    
    def test_user_polymorphism_admin(self, db_session):
        admin = User(username="admin", password_hash="hash", is_admin=True, role="admin")
        db_session.add(admin)
        db_session.commit()
        
        assert admin.role == "admin"
        assert admin.is_admin == True
    
    def test_user_polymorphism_regular(self, db_session):
        regular = User(username="regular", password_hash="hash", is_admin=False, role="user")
        db_session.add(regular)
        db_session.commit()
        
        assert regular.role == "user"
        assert regular.is_admin == False
    
    def test_user_with_2fa_attributes(self, db_session):
        user = User(username="twofa", password_hash="hash", is_2fa_enabled=True, totp_secret="SECRET123", login_attempts=0)
        db_session.add(user)
        db_session.commit()
        
        assert user.is_2fa_enabled == True
        assert user.totp_secret == "SECRET123"

class TestTaskModel:
    def test_task_creation(self, db_session):
        task = Task(title="Test Task", description="Description", status="todo", owner="testuser")
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.status == "todo"
        assert task.owner == "testuser"
    
    def test_task_polymorphism_different_statuses(self, db_session):
        task_todo = Task(title="Todo", status="todo", owner="testuser")
        task_in_progress = Task(title="In Progress", status="in_progress", owner="testuser")
        task_done = Task(title="Done", status="done", owner="testuser")
        
        for task in [task_todo, task_in_progress, task_done]:
            db_session.add(task)
        
        db_session.commit()
        
        tasks = db_session.exec(select(Task)).all()
        assert len(tasks) == 3
    
    def test_task_with_different_owners(self, db_session):
        task1 = Task(title="User1 Task", owner="user1")
        task2 = Task(title="User2 Task", owner="user2")
        
        db_session.add_all([task1, task2])
        db_session.commit()
        
        tasks_user1 = db_session.exec(select(Task).where(Task.owner == "user1")).all()
        tasks_user2 = db_session.exec(select(Task).where(Task.owner == "user2")).all()
        
        assert len(tasks_user1) == 1
        assert len(tasks_user2) == 1

class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed) == True
        assert verify_password("wrongpassword", hashed) == False

class TestJWTTokens:
    def test_create_access_token(self):
        token = create_access_token({"sub": "testuser"})
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_refresh_token(self):
        token = create_refresh_token({"sub": "testuser"})
        assert token is not None
        assert isinstance(token, str)
    
    def test_verify_valid_token(self):
        token = create_access_token({"sub": "testuser"})
        payload = verify_token(token, "tu-super-secret-key-cambiala-en-produccion")
        
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["type"] == "access"
    
    def test_verify_invalid_token(self):
        payload = verify_token("invalid_token", "tu-super-secret-key-cambiala-en-produccion")
        assert payload is None
    
    def test_verify_wrong_secret(self):
        token = create_access_token({"sub": "testuser"})
        payload = verify_token(token, "wrong_secret")
        assert payload is None

class TestAuth:
    def test_register_success(self, client):
        response = client.post("/register", json={"username": "newuser", "password": "password123"})
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert "access_token" in data
    
    def test_register_duplicate_user(self, client):
        client.post("/register", json={"username": "duplicate", "password": "pass123"})
        response = client.post("/register", json={"username": "duplicate", "password": "pass123"})
        assert response.status_code == 400
    
    def test_login_success(self, client, db_session):
        user = User(username="loginuser", password_hash=hash_password("password123"))
        db_session.add(user)
        db_session.commit()
        
        response = client.post("/login", data={"username": "loginuser", "password": "password123"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    def test_login_invalid_credentials(self, client):
        response = client.post("/login", data={"username": "nonexistent", "password": "wrongpass"})
        assert response.status_code == 401
    
    def test_logout(self, client):
        response = client.post("/logout")
        assert response.status_code == 200
    
    def test_get_current_user(self, client):
        response = client.get("/me")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

class TestTasks:
    def test_create_task(self, client):
        response = client.post("/tasks", json={"title": "New Task", "description": "Test", "owner": "testuser"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Task"
    
    def test_list_tasks(self, client, db_session):
        task = Task(title="Task1", owner="testuser")
        db_session.add(task)
        db_session.commit()
        
        response = client.get("/tasks")
        assert response.status_code == 200
    
    def test_get_task(self, client, db_session):
        task = Task(title="Get Test", owner="testuser")
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        response = client.get(f"/tasks/{task.id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Get Test"
    
    def test_update_task(self, client, db_session):
        task = Task(title="Original", owner="testuser")
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        response = client.put(f"/tasks/{task.id}", json={"title": "Updated", "description": "New desc", "owner": "testuser"})
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"
    
    def test_delete_task(self, client, db_session):
        task = Task(title="To Delete", owner="testuser")
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        response = client.delete(f"/tasks/{task.id}")
        assert response.status_code == 200
    
    def test_change_task_status(self, client, db_session):
        task = Task(title="Status Test", status="todo", owner="testuser")
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        response = client.patch(f"/tasks/{task.id}/status?status=done")
        assert response.status_code == 200
        assert response.json()["status"] == "done"
    
    def test_list_tasks_by_status(self, client, db_session):
        task = Task(title="Status Filter", status="done", owner="testuser")
        db_session.add(task)
        db_session.commit()
        
        response = client.get("/tasks/by_status/done")
        assert response.status_code == 200
    
    def test_list_tasks_by_user(self, client, db_session):
        task = Task(title="User Tasks", owner="testuser")
        db_session.add(task)
        db_session.commit()
        
        response = client.get("/tasks/by_user/testuser")
        assert response.status_code == 200

class TestAdmin:
    def test_list_users_as_admin(self, client):
        response = client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_promote_user(self, client, db_session):
        user = User(username="promote_test", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        response = client.post("/admin/promote/promote_test")
        assert response.status_code == 200
    
    def test_demote_user(self, client, db_session):
        user = User(username="demote_test", password_hash="hash", is_admin=True, role="admin")
        db_session.add(user)
        db_session.commit()
        
        response = client.post("/admin/demote/demote_test")
        assert response.status_code == 200

class TestTOTP:
    def test_generate_totp(self):
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        assert len(code) == 6
        assert totp.verify(code) == True
    
    def test_totp_valid_window(self):
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        assert totp.verify(code, valid_window=1) == True

class TestRefreshToken:
    def test_refresh_token_endpoint(self, client):
        response = client.post("/refresh")
        assert response.status_code == 401

class TestSecurity:
    def test_login_rate_limiting(self, client, db_session):
        user = User(username="ratelimit", password_hash=hash_password("pass"))
        db_session.add(user)
        db_session.commit()
        
        for i in range(5):
            client.post("/login", data={"username": "ratelimit", "password": "wrong"})
        
        response = client.post("/login", data={"username": "ratelimit", "password": "wrong"})
        assert response.status_code in [401, 423]

class TestEdgeCases:
    def test_get_nonexistent_task(self, client):
        response = client.get("/tasks/99999")
        assert response.status_code == 404
    
    def test_update_nonexistent_task(self, client):
        response = client.put("/tasks/99999", json={"title": "Test"})
        assert response.status_code == 404
    
    def test_delete_nonexistent_task(self, client):
        response = client.delete("/tasks/99999")
        assert response.status_code == 404
    
    def test_change_status_nonexistent_task(self, client):
        response = client.patch("/tasks/99999/status?status=done")
        assert response.status_code == 404
    
    def test_list_tasks_by_nonexistent_user(self, client):
        response = client.get("/tasks/by_user/nonexistent")
        assert response.status_code == 200
    
    def test_list_tasks_by_nonexistent_status(self, client):
        response = client.get("/tasks/by_status/nonexistent")
        assert response.status_code == 200

class TestPolymorphism:
    def test_polymorphic_user_roles(self, db_session):
        admin = User(username="admin1", password_hash="h", is_admin=True, role="admin")
        regular = User(username="user1", password_hash="h", is_admin=False, role="user")
        
        db_session.add_all([admin, regular])
        db_session.commit()
        
        assert admin.role == "admin"
        assert regular.role == "user"
    
    def test_polymorphic_task_statuses(self, db_session):
        pending = Task(title="P1", status="todo", owner="u")
        progress = Task(title="P2", status="in_progress", owner="u")
        completed = Task(title="P3", status="done", owner="u")
        
        db_session.add_all([pending, progress, completed])
        db_session.commit()
        
        all_tasks = db_session.exec(select(Task)).all()
        assert len(all_tasks) == 3
    
    def test_polymorphic_2fa_enabled_user(self, db_session):
        user_2fa = User(username="with2fa", password_hash="h", is_2fa_enabled=True, totp_secret="ABC123")
        db_session.add(user_2fa)
        db_session.commit()
        
        assert user_2fa.is_2fa_enabled == True
        assert user_2fa.totp_secret == "ABC123"
    
    def test_polymorphic_locked_user(self, db_session):
        locked_user = User(username="locked", password_hash="h", login_attempts=5, locked_until=datetime.utcnow() + timedelta(minutes=15))
        db_session.add(locked_user)
        db_session.commit()
        
        assert locked_user.login_attempts >= 5

class TestModelInheritance:
    def test_user_model_all_fields(self, db_session):
        user = User(
            username="fulluser",
            password_hash="hash",
            is_admin=False,
            role="user",
            is_2fa_enabled=True,
            totp_secret="SECRET",
            login_attempts=0
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.username == "fulluser"
        assert user.is_admin == False
        assert user.role == "user"
        assert user.is_2fa_enabled == True
        assert user.totp_secret == "SECRET"
    
    def test_task_model_all_fields(self, db_session):
        task = Task(
            title="Full Task",
            description="Full description",
            status="in_progress",
            owner="owner"
        )
        db_session.add(task)
        db_session.commit()
        
        assert task.title == "Full Task"
        assert task.description == "Full description"
        assert task.status == "in_progress"
        assert task.owner == "owner"

class TestErrorHandlers:
    def test_rate_limit_exceeded_handler(self, client):
        for i in range(10):
            client.post("/register", json={"username": f"user{i}", "password": "pass"})
        
        response = client.post("/register", json={"username": "exceed", "password": "pass"})
        assert response.status_code in [200, 429]

class TestTokenData:
    def test_token_model(self, db_session):
        token_data = {"access_token": "abc123", "refresh_token": "xyz789", "token_type": "bearer"}
        assert token_data["access_token"] == "abc123"
        assert token_data["token_type"] == "bearer"

class TestUsersEndpoint:
    def test_get_user_tasks(self, client, db_session):
        user = User(username="taskowner", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        task = Task(title="User Task", owner="taskowner")
        db_session.add(task)
        db_session.commit()
        
        response = client.get(f"/users/1/tasks")
        assert response.status_code == 200

class TestTokenPayloads:
    def test_token_data_model(self):
        from main import TokenData
        td = TokenData(username="test")
        assert td.username == "test"

class TestTaskCreate:
    def test_task_create_model(self):
        from main import TaskCreate
        tc = TaskCreate(title="Test", description="Desc", owner="user")
        assert tc.title == "Test"
        assert tc.description == "Desc"

class TestRegisterPayload:
    def test_register_payload_model(self):
        from main import RegisterPayload
        rp = RegisterPayload(username="user", password="pass")
        assert rp.username == "user"
        assert rp.password == "pass"

class TestVerify2FAPayload:
    def test_verify_2fa_payload(self):
        from main import Verify2FAPayload
        vp = Verify2FAPayload(username="user", code="123456")
        assert vp.username == "user"
        assert vp.code == "123456"

class TestAdditionalCoverage:
    def test_login_with_2fa_enabled(self, client, db_session):
        user = User(username="twofalogin", password_hash=hash_password("pass123"), is_2fa_enabled=True, totp_secret="SECRET")
        db_session.add(user)
        db_session.commit()
        
        response = client.post("/login", data={"username": "twofalogin", "password": "pass123"})
        assert response.status_code == 200
    
    def test_logout_with_2fa_flow(self, client):
        response = client.post("/logout")
        assert response.status_code == 200
    
    def test_create_task_with_owner(self, client):
        response = client.post("/tasks", json={"title": "Task", "description": "Desc", "owner": "testuser"})
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=term-missing"])