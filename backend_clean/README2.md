# README2.md - TaskFlow Clean Architecture Backend

## Tabla de Contenidos
1. [Estructura del Proyecto](#estructura-del-proyecto)
2. [Conceptos Implementados](#conceptos-implementados)
3. [Donde Encontrar Cada Concepto](#donde-encontrar-cada-concepto)
4. [Como Ejecutar](#como-ejecutar)
5. [API Endpoints](#api-endpoints)
6. [Testing](#testing)
7. [Patrones de Arquitectura](#patrones-de-arquitectura)
8. [Chatbot y 2FA](#chatbot-y-2fa)

---

## Estructura del Proyecto

```
backend_clean/
├── main.py                          # Punto de entrada FastAPI
├── requirements.txt                 # Dependencias Python
├── pytest.ini                       # Configuración pytest
│
├── src/
│   ├── domain/                      # DOMINIO (innermost layer)
│   │   ├── entities/
│   │   │   ├── base.py             # BaseEntity (ABC) - Clases abstractas
│   │   │   ├── user.py             # User - @property, herencia
│   │   │   └── task.py             # Task - @property, herencia
│   │   ├── value_objects/
│   │   │   ├── email.py            # Value Object Email
│   │   │   ├── password.py         # Value Object Password
│   │   │   └── task_status.py     # Value Object TaskStatus
│   │   └── repositories/
│   │       ├── irepositories.py     # IUserRepository (abstract class)
│   │       └── itask_repository.py # ITaskRepository (abstract class)
│   │
│   ├── application/                # APPLICATION (用例)
│   │   ├── dtos/
│   │   │   ├── user_dto.py        # UserDTO, CreateUserDTO, UpdateUserDTO
│   │   │   ├── task_dto.py        # TaskDTO, CreateTaskDTO
│   │   │   ├── token_dto.py       # TokenDTO (Pydantic)
│   │   │   └── response_dto.py    # Response DTOs
│   │   └── use_cases/
│   │       ├── create_user_usecase.py
│   │       ├── authenticate_user_usecase.py
│   │       ├── create_task_usecase.py
│   │       ├── update_task_usecase.py
│   │       ├── delete_task_usecase.py
│   │       ├── list_tasks_usecase.py
│   │       ├── get_task_usecase.py
│   │       └── complete_task_usecase.py
│   │
│   ├── infrastructure/              # INFRAESTRUCTURA
│   │   ├── auth/
│   │   │   ├── jwt_handler.py     # JWT tokens (create, verify)
│   │   │   └── password_handler.py # Password hashing bcrypt
│   │   ├── database/
│   │   │   ├── base.py         # Base declarative SQLAlchemy
│   │   │   ├── session.py      # get_db dependency
│   │   │   └── engine.py    # SQLAlchemy engine
│   │   ├── models/
│   │   │   ├── user_model.py  # SQLAlchemy User ORM
│   │   │   └── task_model.py # SQLAlchemy Task ORM
│   │   └── repositories/
│   │       ├── sqlalchemy_user_repo.py
│   │       └── sqlalchemy_task_repo.py
│   │
│   └── presentation/              # PRESENTACIÓN
│       ├── api/
│       │   ├── app.py         # FastAPI app
│       │   └── endpoints/
│       │       ├── auth.py    # /auth/register, /auth/login
│       │       └── tasks.py  # CRUD tasks
│       └── dependencies/
│           └── injection.py   # Dependency Injection
│
├── tests/
│   ├── conftest.py           # Fixtures pytest
│   ├── unit/
│   │   ├── test_entities.py  # Tests unitarios entidades
│   │   └── test_use_cases.py # Tests unitarios use cases
│   ├─��� integration/
│   │   └── test_api.py     # Tests de integración API
│   └── bdd/
│       ├── features/
│       │   └── *.feature  # Behave feature files
│       └── steps/
│           ├── user_steps.py # Steps Gherkin para usuarios
│           └── task_steps.py # Steps Gherkin para tareas
│
└── alembic/                 # Migraciones Alembic
    ├── env.py
    └── versions/
```

---

## Conceptos Implementados

### 1. Clases y Objetos / __init__ / self
**Ubicación:** `src/domain/entities/user.py`, `src/domain/entities/task.py`

```python
class User(BaseEntity):
    def __init__(self, username: str, email: str, password_hash: str = ""):
        self._username = username  # self referencia la instancia
        self._email = email
        self._password_hash = password_hash
```

### 2. Encapsulamiento con @property
**Ubicación:** `src/domain/entities/user.py`, `src/domain/entities/task.py`

```python
# User entity - encapsulamiento completo
@property
def password_hash(self) -> str:
    """Solo lectura desde afuera - encapsulamiento"""
    return self._password_hash

@property
def is_admin(self) -> bool:
    return self._role == "admin"

@username.setter
def username(self, value: str):
    """Set con validación"""
    if len(value) < 3:
        raise ValueError("Username muy corto")
    self._username = value
```

### 3. Herencia
**Ubicación:** `src/domain/entities/base.py` → `user.py`, `task.py`

```python
# base.py - clase padre
class BaseEntity(ABC):
    def __init__(self, id: str = None):
        self._id = id or str(uuid.uuid4())
    
    @property
    def id(self) -> str:
        return self._id

# user.py - hereda de BaseEntity
class User(BaseEntity):
    def __init__(self, username: str, ...):
        super().__init__()  # llama al constructor padre
```

### 4. Polimorfismo e Interfaces Abstractas
**Ubicación:** `src/domain/repositories/irepositories.py`

```python
from abc import ABC, abstractmethod

class IUserRepository(ABC):
    """Interfaz abstracta - define contrato"""
    @abstractmethod
    def create(self, user: User) -> User: pass
    
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]: pass

# Implementación concreta - polimorfismo
class SQLAlchemyUserRepository(IUserRepository):
    def create(self, user: User) -> User:
        # implementación específica
```

### 5. Clases Abstractas
**Ubicación:** `src/domain/entities/base.py`, `src/domain/repositories/irepositories.py`

```python
from abc import ABC, abstractmethod

class BaseEntity(ABC):  # ABC = Abstract Base Class
    @abstractmethod
    def to_dict(self) -> dict: pass
```

### 6. Intro TDD / Ciclo Red-Green-Refactor
**Ubicación:** `tests/unit/test_entities.py`

```python
# RED: Escribir test que falla
def test_user_encapsulation():
    user = User(username="test", password="secret")
    assert user.password_hash != "secret"  # Falla hasta implementar

# GREEN: Implementar mínimo para pasar
def set_password(self, password):
    self._password_hash = hash(password)

# REFACTOR: Mejorar código manteniendo_tests pasando
```

### 7. pytest: fixtures, parametrize
**Ubicación:** `tests/conftest.py`

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
def engine():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    return test_engine

@pytest.fixture(scope="function")
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

# parametrize
@pytest.mark.parametrize("username,email", [
    ("user1", "user1@test.com"),
    ("user2", "user2@test.com"),
])
def test_user_creation(username, email):
    user = User(username=username, email=email)
    assert user.username == username
```

### 8. BDD con behave / Gherkin
**Ubicación:** `tests/bdd/steps/user_steps.py`, `tests/bdd/features/`

```python
# steps/user_steps.py - implementación Gherkin
from behave import given, when, then

@given('I am on the registration page')
def step_registration_page(context):
    context.path = "/auth/register"

@when('I submit the registration form')
def step_submit_form(context):
    response = client.post(context.path, json=context.data)

@then('I should see a success message')
def step_success(context):
    assert context.status_code == 201
```

Feature file Gherkin:
```gherkin
Feature: User Registration

  Scenario: Register new user
    Given I am on the registration page
    When I fill in username "newuser"
    And I fill in email "newuser@test.com"
    And I fill in password "SecurePass123"
    And I submit the registration form
    Then I should see a success message
```

### 9. DDD / Repository Pattern
**Ubicación:** `src/domain/repositories/` + `src/infrastructure/repositories/`

```python
# domain/repositories/irepositories.py - Interfaz
class IUserRepository(ABC):
    @abstractmethod
    def create(self, user: User) -> User: pass

# infrastructure/repositories/sqlalchemy_user_repo.py - Implementación
class SQLAlchemyUserRepository(IUserRepository):
    def create(self, user: User) -> User:
        db_user = UserModel.from_entity(user)
        self.session.add(db_user)
        return user
```

### 10. FastAPI / Rutas / Pydantic
**Ubicación:** `src/presentation/api/app.py`, `src/presentation/api/endpoints/`

```python
# app.py
from fastapi import FastAPI
app = FastAPI(title="TaskFlow API")

# endpoints/auth.py
from fastapi import APIRouter, Depends
router = APIRouter()

@router.post("/auth/register")
def register(payload: CreateUserDTO):
    return {"success": True}

# endpoints/tasks.py
@router.get("/tasks/")
def list_tasks(current_user: User = Depends(get_current_user)):
    return tasks
```

### 11. Pydantic y Validación
**Ubicación:** `src/application/dtos/`

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class CreateUserDTO(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr  # Validación automática de email
    password: str = Field(min_length=8)
    
    class Config:
        json_schema_extra = {"example": {...}}

class UserDTO(BaseModel):
    id: str
    username: str
    email: EmailStr
    is_active: bool
```

### 12. Dependency Injection / SQLAlchemy
**Ubicación:** `src/presentation/dependencies/injection.py`

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_repository(
    db: Session = Depends(get_db)
) -> IUserRepository:
    return SQLAlchemyUserRepository(db)

def get_current_user(
    token: str = Depends(get_token),
    user_repo: IUserRepository = Depends(get_user_repository)
) -> User:
    # FastAPI inyecta las dependencias
```

### 13. CRUD Completo y Auth
**Ubicación:** `src/presentation/api/endpoints/`

```python
# Auth endpoints
@router.post("/auth/register")
@router.post("/auth/login")

# Tasks CRUD
@router.get("/tasks/")
@router.get("/tasks/{task_id}")
@router.post("/tasks/")
@router.put("/tasks/{task_id}")
@router.delete("/tasks/{task_id}")
@router.patch("/tasks/{task_id}/complete")
```

### 14. Práctica Auth / JWT
**Ubicación:** `src/infrastructure/auth/jwt_handler.py`

```python
from jose import jwt
from datetime import datetime, timedelta

class JWTHandler:
    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_token(self, token: str) -> dict:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

### 15. SQLAlchemy ORM / Modelos
**Ubicación:** `src/infrastructure/models/`

```python
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    
    tasks = relationship("TaskModel", back_populates="owner")
```

### 16. Alembic / Migraciones
**Ubicación:** `alembic/`

```powershell
# Crear migración
alembic revision --autogenerate -m "add user role"

# Aplicar
alembic upgrade head

# Rollback
alembic downgrade -1
```

### 17. SQLAlchemy Relaciones
**Ubicación:** `src/infrastructure/models/`

```python
# One-to-Many: User -> Tasks
class UserModel(Base):
    tasks = relationship("TaskModel", back_populates="owner")

class TaskModel(Base):
    owner_id = Column(String, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="tasks")
```

### 18. CRUD con SQLAlchemy
**Ubicación:** `src/infrastructure/repositories/`

```python
class SQLAlchemyUserRepository(IUserRepository):
    def create(self, user: User) -> User:
        model = UserModel.from_entity(user)
        self.session.add(model)
        self.session.commit()
        return user
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.session.get(UserModel, user_id)
    
    def update(self, user: User) -> User:
        self.session.commit()
        return user
    
    def delete(self, user_id: str) -> bool:
        user = self.session.get(UserModel, user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False
```

### 19. Repository Pattern
**Ubicación:** `src/domain/repositories/` + `src/infrastructure/`

```
domain/repositories/     → Interfaz (contrato)
application/use_cases/  → Usa la interfaz
infrastructure/       → Implementa la interfaz
```

### 20. Clean Architecture + JWT
**Capas:**
```
presentation/  → API, Endpoints, DI
application/ → DTOs, Use Cases
domain/      → Entities, Value Objects, Interfaces
infrastructure/ → Auth, DB, Models
```

### 21. DTOs y Serialización
**Ubicación:** `src/application/dtos/`

```python
class UserDTO(BaseModel):
    id: str
    username: str
    email: EmailStr
    
    class Config:
        from_attributes = True

# Serialización automática
user_dto = UserDTO.model_validate(user_entity)
```

### 22. API REST Avanzada
**Ubicación:** `src/presentation/api/endpoints/`

```python
from fastapi import HTTPException, status, Query

@router.get("/tasks/", response_model=List[TaskDTO])
def list_tasks(
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    return tasks
```

### 23. Testing de Integración
**Ubicación:** `tests/integration/test_api.py`

```python
from fastapi.testclient import TestClient

def test_register_endpoint(client):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@test.com",
        "password": "password123"
    })
    assert response.status_code == 201
    assert response.json()["success"] == True
```

---

## Donde Encontrar Cada Concepto

| Concepto | Ubicación |
|---------|-----------|
| **Clases y Objetos / __init__ / self** | `src/domain/entities/user.py`, `task.py` |
| **Encapsulamiento @property** | `src/domain/entities/user.py`, `task.py` |
| **Herencia (BaseEntity)** | `src/domain/entities/base.py` |
| **Polimorfismo** | `src/domain/repositories/` |
| **Clases Abstractas ABC** | `src/domain/entities/base.py`, `src/domain/repositories/irepositories.py` |
| **Intro TDD** | `tests/unit/test_entities.py` |
| **pytest fixtures** | `tests/conftest.py` |
| **pytest parametrize** | `tests/unit/test_use_cases.py` |
| **BDD/Behave** | `tests/bdd/steps/`, `tests/bdd/features/` |
| **DDD Repository Pattern** | `src/domain/repositories/` + `src/infrastructure/repositories/` |
| **FastAPI** | `src/presentation/api/app.py` |
| **Pydantic** | `src/application/dtos/` |
| **Dependency Injection** | `src/presentation/dependencies/injection.py` |
| **JWT** | `src/infrastructure/auth/jwt_handler.py` |
| **SQLAlchemy ORM** | `src/infrastructure/models/` |
| **Alembic** | `alembic/` |
| **Relaciones SQLAlchemy** | `src/infrastructure/models/user_model.py`, `task_model.py` |
| **CRUD** | `src/infrastructure/repositories/` |
| **Clean Architecture** | Carpetas `domain/`, `application/`, `infrastructure/`, `presentation/` |
| **DTOs** | `src/application/dtos/` |
| **API REST** | `src/presentation/api/endpoints/` |
| **Integration Tests** | `tests/integration/test_api.py` |

---

## Chatbot y 2FA

### Chatbot
**Ubicación (Backend Original):** `backend/main.py`

```python
# Endpoint chatbot
@app.post("/chatbot")
def chatbot(payload: ChatbotPayload, current_user: User = Depends(get_current_user)):
    # Procesa mensajes del chatbot

@app.post("/chatbot/v2")
def chatbot_v2(payload: ChatbotPayload, current_user: User = Depends(get_current_user)):
    # Versión mejorada del chatbot
```

### 2FA (Two-Factor Authentication)
**Ubicación (Backend Original):** `backend/main.py`, `backend/app/models.py`

```python
# Model - app/models.py
class User(SQLModel, table=True):
    is_2fa_enabled: bool = Field(default=False)
    totp_secret: Optional[str] = Field(default=None)
    login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)

# Endpoints - main.py
@app.post("/2fa/setup")
def setup_2fa(current_user: User = Depends(get_current_user)):
    """Genera secreto TOTP para configurar 2FA"""

@app.post("/2fa/enable")
def enable_2fa(payload: Verify2FAPayload, current_user: User = Depends(get_current_user)):
    """Habilita 2FA después de verificar código"""

@app.post("/2fa/disable")
def disable_2fa(payload: Verify2FAPayload, current_user: User = Depends(get_current_user)):
    """Deshabilita 2FA"""

@app.post("/login/2fa")
def login_2fa(payload: Verify2FAPayload):
    """Verifica código 2FA después del login"""
```

---

## Como Ejecutar

### 1. Backend Clean (Puerto 8010)
```powershell
cd C:\Users\User\taskflow_app\backend_clean
.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8010
```

### 2. Backend Original (Puerto 8000) - Con Chatbot y 2FA
```powershell
cd C:\Users\User\taskflow_app\backend
.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Frontend (Puerto 5181)
```powershell
cd C:\Users\User\taskflow_app\frontend
npm run dev
```

### 4. Tests
```powershell
# Unit tests
.venv\Scripts\python.exe -m pytest tests/unit/ -v

# Integration tests
.venv\Scripts\python.exe -m pytest tests/integration/ -v

# BDD
.venv\Scripts\python.exe -m behave tests/bdd/
```

---

## API Endpoints

### Backend Original (Puerto 8000) - Con Chatbot y 2FA
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/register` | Registrar usuario |
| POST | `/login` | Login básico |
| POST | `/login/2fa` | Verificar кодigo 2FA |
| POST | `/2fa/setup` | Configurar 2FA |
| POST | `/2fa/enable` | Habilitar 2FA |
| POST | `/2fa/disable` | Deshabilitar 2FA |
| POST | `/chatbot` | Chatbot básico |
| POST | `/chatbot/v2` | Chatbot mejorado |
| GET | `/users` | Listar usuarios |

### Backend Clean (Puerto 8010)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/auth/register` | Registrar |
| POST | `/auth/login` | Login JWT |
| GET | `/auth/me` | Usuario actual |
| GET | `/tasks/` | Listar tareas |
| POST | `/tasks/` | Crear tarea |
| PUT | `/tasks/{id}` | Actualizar |
| DELETE | `/tasks/{id}` | Eliminar |
| PATCH | `/tasks/{id}/complete` | Completar |

---

**Generado:** 28/04/2026
**Versión:** 2.0.0