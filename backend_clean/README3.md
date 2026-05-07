# README3.md - Mapa tecnico real de TaskFlow

Este documento mejora `README2.md` y ubica cada concepto en el proyecto real.

Hay dos backends importantes:

- `backend_clean/`: backend con Clean Architecture, DDD, SQLAlchemy clasico, DTOs, use cases, repositorios, JWT y pruebas unitarias/integracion/BDD.
- `backend/`: backend principal usado por el frontend actual, con FastAPI en un solo archivo, SQLModel, chatbot Flowi, 2FA, subida de imagenes y endpoints usados por la UI.

El frontend principal esta en `frontend/src/App_auth.jsx`.

## Estructura principal

```text
taskflow_app/
+-- backend/
|   +-- main.py                 # API principal usada por el frontend actual
|   +-- app/
|   |   +-- models.py           # Modelos SQLModel: User y Task
|   |   +-- db.py               # Engine SQLModel/MySQL
|   +-- test_main.py            # Tests del backend principal
+-- backend_clean/
|   +-- main.py                 # Entrada FastAPI clean architecture
|   +-- src/
|   |   +-- domain/             # Entidades, value objects, interfaces
|   |   +-- application/        # DTOs y use cases
|   |   +-- infrastructure/     # SQLAlchemy, JWT, password hashing, repos
|   |   +-- presentation/       # Endpoints FastAPI y dependency injection
|   +-- tests/                  # Unit, integration y BDD
|   +-- alembic/                # Migraciones Alembic
|   +-- README3.md              # Este documento
+-- frontend/
    +-- src/
        +-- App_auth.jsx        # UI principal, panel admin y chatbot Flowi
        +-- api.js              # Cliente HTTP
        +-- styles.css          # Estilos
```

## Donde esta cada concepto

| Concepto | Donde esta | Estado |
|---|---|---|
| FastAPI | `backend/main.py`, `backend_clean/main.py`, `backend_clean/src/presentation/api/app.py` | Implementado |
| Rutas REST | `backend/main.py`; `backend_clean/src/presentation/api/endpoints/auth.py`; `backend_clean/src/presentation/api/endpoints/tasks.py` | Implementado |
| Pydantic DTOs | `backend/main.py` para payloads simples; `backend_clean/src/application/dtos/` para DTOs limpios | Implementado |
| SQLAlchemy clasico | `backend_clean/src/infrastructure/database/`, `backend_clean/src/infrastructure/models/`, `backend_clean/src/infrastructure/repositories/` | Implementado |
| SQLModel | `backend/app/models.py`, `backend/app/db.py`, `backend/main.py` | Implementado |
| JWT | `backend/main.py`; `backend_clean/src/infrastructure/auth/jwt_handler.py` | Implementado |
| Password hashing | `backend/main.py`; `backend_clean/src/infrastructure/auth/password_handler.py` | Implementado |
| Dependency Injection | `backend/main.py` con `Depends`; `backend_clean/src/presentation/dependencies/injection.py` | Implementado |
| Repository Pattern | `backend_clean/src/domain/repositories/` + `backend_clean/src/infrastructure/repositories/` | Implementado |
| Clean Architecture | `backend_clean/src/domain`, `application`, `infrastructure`, `presentation` | Implementado |
| DDD entities | `backend_clean/src/domain/entities/` | Implementado |
| Value Objects | `backend_clean/src/domain/value_objects/` | Implementado |
| Use Cases | `backend_clean/src/application/use_cases/` | Implementado |
| Herencia | `backend_clean/src/domain/entities/base.py` -> `user.py` y `task.py` | Implementado |
| Clases abstractas | `backend_clean/src/domain/entities/base.py`, `backend_clean/src/domain/repositories/` | Implementado |
| Polimorfismo | Interfaces `IUserRepository`/`ITaskRepository` y repos SQLAlchemy concretos | Implementado |
| Relaciones SQLAlchemy | `backend_clean/src/infrastructure/models/task_model.py` usa `ForeignKey("users.id")`; no hay `relationship()` explicito | Parcial |
| Alembic | `backend_clean/alembic.ini`, `backend_clean/alembic/`, `backend_clean/migrations/` | Implementado |
| Tests pytest | `backend/test_main.py`, `backend_clean/tests/unit/`, `backend_clean/tests/integration/` | Implementado |
| Fixtures pytest | `backend_clean/tests/conftest.py`, `backend/test_main.py` | Implementado |
| BDD/Behave | `backend_clean/tests/bdd/features/`, `backend_clean/tests/bdd/steps/` | Implementado |
| Chatbot | `backend/main.py` endpoint `/chatbot`; UI en `frontend/src/App_auth.jsx` | Implementado |
| 2FA | `backend/main.py`, `backend/app/models.py` | Implementado en backend principal |
| Admin | `backend/main.py`, `frontend/src/App_auth.jsx` | Implementado |
| Subida de imagenes | `backend/main.py` endpoints `/tasks/{task_id}/image`; UI en `App_auth.jsx` | Implementado |

## Backend principal: `backend/`

Este es el backend que usa el frontend actual.

### FastAPI y rutas

Archivo: `backend/main.py`

Ejemplos de rutas:

- `POST /register`
- `POST /login`
- `POST /login/2fa`
- `POST /refresh`
- `GET /me`
- `GET /users`
- `DELETE /users/{user_id}`
- `GET /tasks`
- `POST /tasks`
- `PUT /tasks/{task_id}`
- `DELETE /tasks/{task_id}`
- `PATCH /tasks/{task_id}/status`
- `POST /tasks/{task_id}/image`
- `GET /tasks/{task_id}/image`
- `POST /chatbot`
- `POST /chatbot/v2`

### SQLModel y base de datos

Archivos:

- `backend/app/models.py`
- `backend/app/db.py`
- `backend/main.py`

`backend/app/models.py` define:

- `User(SQLModel, table=True)`
- `Task(SQLModel, table=True)`

`backend/app/db.py` crea el engine:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:123456789@localhost:3306/taskflow")
engine = create_engine(DATABASE_URL, echo=False)
```

`backend/main.py` usa `Session(engine)` y `select(...)` para CRUD.

### JWT

Archivo: `backend/main.py`

Funciones principales:

- `create_access_token`
- `create_refresh_token`
- `verify_token`
- `get_current_user`

Libreria usada:

```python
from jose import JWTError, jwt
```

### Seguridad y auth

Archivo: `backend/main.py`

Incluye:

- `OAuth2PasswordBearer(tokenUrl="login")`
- `CryptContext` con bcrypt
- `require_admin`
- bloqueo por intentos de login con `login_attempts` y `locked_until`
- tokens access y refresh

### 2FA

Archivos:

- `backend/main.py`
- `backend/app/models.py`

Campos en `User`:

- `is_2fa_enabled`
- `totp_secret`

Endpoints:

- `POST /2fa/setup`
- `POST /2fa/enable`
- `POST /2fa/disable`
- `POST /login/2fa`

### Chatbot Flowi

Archivos:

- Backend: `backend/main.py`
- Frontend: `frontend/src/App_auth.jsx`
- Estilos: `frontend/src/styles.css`

Nombre visible actual: **Flowi**.

Funciones de Flowi:

- crear tareas con lenguaje natural
- completar tareas
- eliminar tareas
- buscar tareas
- listar tareas
- cambiar estado
- pedir descripcion despues de crear tarea
- recordar contexto de foto o descripcion pendiente
- guiar subida de imagenes

El endpoint principal es:

```python
@app.post("/chatbot")
def chatbot(payload: ChatbotPayload, current_user: User = Depends(get_current_user)):
```

La UI de Flowi esta en `frontend/src/App_auth.jsx`, especialmente:

- estado `chatbotMessages`
- `handleChatbotSubmit`
- `handleChatbotPhotoPick`
- `handleChatbotImageUpload`
- ventana `.chatbot-window`

### Admin y eliminacion de usuarios

Archivo: `backend/main.py`

Endpoints:

- `GET /users`
- `POST /admin/promote/{username}`
- `POST /admin/demote/{username}`
- `DELETE /users/{user_id}`

La proteccion se hace con:

```python
def require_admin(current_user: User = Depends(get_current_user)):
```

La UI esta en `frontend/src/App_auth.jsx`, vista `admin`.

## Backend clean: `backend_clean/`

Este backend si contiene la arquitectura por capas descrita en `README2.md`.

### Domain

Carpeta: `backend_clean/src/domain/`

Contiene la logica de dominio independiente de FastAPI y SQLAlchemy.

Archivos importantes:

- `entities/base.py`
- `entities/user.py`
- `entities/task.py`
- `value_objects/email.py`
- `value_objects/password.py`
- `value_objects/task_status.py`
- `repositories/irepositories.py`
- `repositories/itask_repository.py`

### Herencia

Archivos:

- `backend_clean/src/domain/entities/base.py`
- `backend_clean/src/domain/entities/user.py`
- `backend_clean/src/domain/entities/task.py`

`BaseEntity` es la clase padre. `User` y `Task` heredan de ella.

### Clases abstractas

Archivos:

- `backend_clean/src/domain/entities/base.py`
- `backend_clean/src/domain/repositories/irepositories.py`
- `backend_clean/src/domain/repositories/itask_repository.py`

Se usa `ABC` y `@abstractmethod`.

### Polimorfismo

El polimorfismo aparece cuando los use cases trabajan contra interfaces o protocolos, y la infraestructura entrega implementaciones concretas.

Contratos:

- `backend_clean/src/domain/repositories/irepositories.py`
- `backend_clean/src/domain/repositories/itask_repository.py`
- `backend_clean/src/application/use_cases/user_entities.py`
- `backend_clean/src/application/use_cases/task_entities.py`

Implementaciones:

- `backend_clean/src/infrastructure/repositories/sqlalchemy_user_repo.py`
- `backend_clean/src/infrastructure/repositories/sqlalchemy_task_repo.py`

### Application

Carpeta: `backend_clean/src/application/`

Contiene DTOs y casos de uso.

DTOs:

- `dtos/user_dto.py`
- `dtos/task_dto.py`
- `dtos/token_dto.py`
- `dtos/response_dto.py`

Use cases:

- `use_cases/create_user_usecase.py`
- `use_cases/authenticate_user_usecase.py`
- `use_cases/create_task_usecase.py`
- `use_cases/update_task_usecase.py`
- `use_cases/delete_task_usecase.py`
- `use_cases/list_tasks_usecase.py`
- `use_cases/get_task_usecase.py`
- `use_cases/complete_task_usecase.py`

### Infrastructure

Carpeta: `backend_clean/src/infrastructure/`

Contiene detalles tecnicos.

Base de datos:

- `database/session.py`
- `database/base.py`
- `database/engine.py`

Modelos SQLAlchemy:

- `models/user_model.py`
- `models/task_model.py`

Repositorios:

- `repositories/sqlalchemy_user_repo.py`
- `repositories/sqlalchemy_task_repo.py`

Auth:

- `auth/jwt_handler.py`
- `auth/password_handler.py`

### SQLAlchemy

Archivos:

- `backend_clean/src/infrastructure/database/session.py`
- `backend_clean/src/infrastructure/database/engine.py`
- `backend_clean/src/infrastructure/models/user_model.py`
- `backend_clean/src/infrastructure/models/task_model.py`
- `backend_clean/src/infrastructure/repositories/sqlalchemy_user_repo.py`
- `backend_clean/src/infrastructure/repositories/sqlalchemy_task_repo.py`

Usa:

- `create_engine`
- `sessionmaker`
- `declarative_base`
- `Column`
- `String`
- `Boolean`
- `DateTime`
- `ForeignKey`

Nota: `TaskModel` tiene `owner_id = Column(String, ForeignKey("users.id"))`, pero no se encontro `relationship()` explicito entre usuario y tareas. Por eso la relacion SQLAlchemy esta como clave foranea, no como relacion ORM navegable.

### JWT en backend_clean

Archivo:

- `backend_clean/src/infrastructure/auth/jwt_handler.py`

Usa:

- `create_access_token`
- `create_refresh_token`
- `verify_token`
- `python-jose`

Tambien se usa desde:

- `backend_clean/src/application/use_cases/authenticate_user_usecase.py`
- `backend_clean/src/presentation/dependencies/injection.py`
- `backend_clean/src/presentation/api/endpoints/auth.py`

### Presentation

Carpeta: `backend_clean/src/presentation/`

Endpoints:

- `api/endpoints/auth.py`
- `api/endpoints/tasks.py`

Dependency injection:

- `dependencies/injection.py`

Entrada de app:

- `backend_clean/main.py`
- `backend_clean/src/presentation/api/app.py`

## Testing

### Backend principal

Archivo:

- `backend/test_main.py`

Incluye pruebas de:

- modelos `User` y `Task`
- password hashing
- JWT
- auth
- CRUD tasks
- admin
- 2FA/TOTP
- edge cases
- polimorfismo de roles y estados

Comando:

```powershell
python -m pytest backend/test_main.py -v
```

### Backend clean

Archivos:

- `backend_clean/tests/conftest.py`
- `backend_clean/tests/unit/test_entities.py`
- `backend_clean/tests/unit/test_use_cases.py`
- `backend_clean/tests/integration/test_api.py`
- `backend_clean/tests/bdd/features/`
- `backend_clean/tests/bdd/steps/`

Incluye:

- unit tests
- integration tests con `TestClient`
- BDD con Gherkin y Behave
- fixtures de pytest
- mocks de repositorios y handlers

Comandos:

```powershell
cd backend_clean
python -m pytest tests/ -v
python -m behave tests/bdd/
```

## Endpoints principales

### Backend principal (`backend/`, puerto usado actualmente: 8010)

```text
POST   /register
POST   /login
POST   /login/2fa
POST   /refresh
GET    /me
GET    /users
DELETE /users/{user_id}
POST   /admin/promote/{username}
POST   /admin/demote/{username}
GET    /tasks
POST   /tasks
GET    /tasks/{task_id}
PUT    /tasks/{task_id}
DELETE /tasks/{task_id}
PATCH  /tasks/{task_id}/status
POST   /tasks/{task_id}/image
GET    /tasks/{task_id}/image
POST   /chatbot
POST   /chatbot/v2
POST   /2fa/setup
POST   /2fa/enable
POST   /2fa/disable
```

### Backend clean (`backend_clean/`)

```text
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
GET    /auth/me
POST   /tasks/
GET    /tasks/
GET    /tasks/{task_id}
PUT    /tasks/{task_id}
DELETE /tasks/{task_id}
POST   /tasks/{task_id}/complete
GET    /
GET    /health
```

## Como ejecutar

### Backend principal usado por el frontend

```powershell
cd C:\Users\User\taskflow_app\backend
python -m uvicorn main:app --host 127.0.0.1 --port 8010
```

### Frontend

```powershell
cd C:\Users\User\taskflow_app\frontend
npm run dev
```

URL:

```text
http://localhost:5181
```

### Backend clean

```powershell
cd C:\Users\User\taskflow_app\backend_clean
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8010
```

Nota: no ejecutes `backend/` y `backend_clean/` al mismo tiempo en el mismo puerto.

## Resumen de verificacion solicitada

- SQLAlchemy: si, en `backend_clean/src/infrastructure/...`.
- SQLModel: si, en `backend/app/models.py` y `backend/app/db.py`.
- Herencia: si, en `backend_clean/src/domain/entities/`.
- Polimorfismo: si, por interfaces/repositorios en `backend_clean`.
- JWT: si, en `backend/main.py` y `backend_clean/src/infrastructure/auth/jwt_handler.py`.
- FastAPI: si, en ambos backends.
- Pydantic: si, en ambos backends.
- CRUD: si, en ambos backends.
- Tests: si, en `backend/test_main.py` y `backend_clean/tests/`.
- BDD: si, en `backend_clean/tests/bdd/`.
- Chatbot: si, en `backend/main.py` y `frontend/src/App_auth.jsx`.
- Nombre nuevo del chatbot: Flowi.

## Bloques de codigo exactos por concepto

Esta seccion muestra el bloque real donde se encuentra cada punto importante.

### 1. Clases, objetos, `__init__` y `self`

Archivo: `backend_clean/src/domain/entities/user.py`

```python
class User(BaseEntity):
    """
    User entity representing a system user with authentication and authorization.
    Inherits from BaseEntity and encapsulates password hashing.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        username: str = "",
        email: str = "",
        password_hash: str = "",
        role: str = "user",
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> None:
        super().__init__(id, created_at, updated_at)
        self._username = username
        self._email = email
        self._password_hash = password_hash
        self._role = role
        self._is_active = is_active
```

### 2. Encapsulamiento con `@property`

Archivo: `backend_clean/src/domain/entities/user.py`

```python
@property
def password_hash(self) -> str:
    """
    Encapsulated password hash - read-only from outside.
    Returns the hash for verification but never exposes raw password.
    """
    return self._password_hash

def set_password(self, password_hash: str) -> None:
    """Set password hash internally."""
    self._password_hash = password_hash
    self.update_timestamp()
```

Otro ejemplo con validacion:

```python
@username.setter
def username(self, value: str) -> None:
    """Set username with validation."""
    if not value or len(value) < 3:
        raise ValueError("Username must be at least 3 characters")
    self._username = value
    self.update_timestamp()
```

### 3. Herencia

Clase padre.

Archivo: `backend_clean/src/domain/entities/base.py`

```python
class BaseEntity(ABC):
    """
    Abstract base entity providing common attributes and behavior
    for all domain entities. Implements core entity functionality.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> None:
        self._id = id or str(uuid.uuid4())
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or datetime.utcnow()
```

Clase hija.

Archivo: `backend_clean/src/domain/entities/user.py`

```python
class User(BaseEntity):
    def __init__(self, id: Optional[str] = None, username: str = "", ...):
        super().__init__(id, created_at, updated_at)
        self._username = username
```

### 4. Clase abstracta

Archivo: `backend_clean/src/domain/entities/base.py`

```python
@abstractmethod
def to_dict(self) -> dict[str, Any]:
    """Convert entity to dictionary representation."""
    pass
```

### 5. Polimorfismo con interfaces y repositorios

Contrato abstracto.

Archivo: `backend_clean/src/domain/repositories/irepositories.py`

```python
class IUserRepository(ABC):
    """
    Abstract repository interface for User entity.
    Defines the contract for user persistence operations.
    """
    
    @abstractmethod
    def create(self, user: User) -> User:
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        pass
```

Implementacion concreta.

Archivo: `backend_clean/src/infrastructure/repositories/sqlalchemy_user_repo.py`

```python
class SQLAlchemyUserRepository(IUserRepository):
    """
    SQLAlchemy implementation of IUserRepository.
    """
    
    def __init__(self, session: Session) -> None:
        self._session = session
    
    def create(self, user: User) -> User:
        """Create a new user."""
        model = self._to_model(user)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)
```

El polimorfismo ocurre porque el caso de uso depende del contrato, no de SQLAlchemy directamente.

Archivo: `backend_clean/src/application/use_cases/authenticate_user_usecase.py`

```python
def __init__(
    self,
    user_repository: IUserRepositoryProtocol,
    password_handler: IPasswordHandler,
    token_handler: ITokenHandler
) -> None:
    self._user_repository = user_repository
    self._password_handler = password_handler
    self._token_handler = token_handler
```

### 6. SQLAlchemy engine, session y base declarativa

Archivo: `backend_clean/src/infrastructure/database/session.py`

```python
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./taskflow.db"

metadata = MetaData()

Base = declarative_base(metadata=metadata)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### 7. SQLAlchemy ORM: modelo User

Archivo: `backend_clean/src/infrastructure/models/user_model.py`

```python
class UserModel(Base):
    """SQLAlchemy model for User."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 8. SQLAlchemy ORM: modelo Task y ForeignKey

Archivo: `backend_clean/src/infrastructure/models/task_model.py`

```python
class TaskModel(Base):
    """SQLAlchemy model for Task."""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending", index=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

Nota: hay relacion por clave foranea con `ForeignKey("users.id")`, pero no hay `relationship()` explicito.

### 9. SQLModel en backend principal

Archivo: `backend/app/models.py`

```python
class User(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    is_admin: bool = Field(default=False)
    role: str = Field(default="user")
    is_2fa_enabled: bool = Field(default=False)
    totp_secret: Optional[str] = Field(default=None)
    login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)

class Task(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    status: str = "todo"
    owner: Optional[str] = Field(default=None, index=True)
    image: Optional[str] = Field(default=None, nullable=True)
    priority: str = Field(default="media")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
```

### 10. SQLModel engine con MySQL

Archivo: `backend/app/db.py`

```python
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:123456789@localhost:3306/taskflow")
engine = create_engine(DATABASE_URL, echo=False)
```

### 11. JWT en backend clean

Archivo: `backend_clean/src/infrastructure/auth/jwt_handler.py`

```python
class JWTHandler:
    """
    JWT token handler for creating and verifying tokens.
    """
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create an access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a token."""
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm]
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
```

### 12. JWT en backend principal

Archivo: `backend/main.py`

```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, secret_key: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 13. Dependency Injection con FastAPI

Archivo: `backend_clean/src/presentation/dependencies/injection.py`

```python
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
```

Admin:

```python
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
```

### 14. Pydantic DTOs

Archivo: `backend_clean/src/application/dtos/user_dto.py`

```python
class CreateUserDTO(BaseModel):
    """
    Data Transfer Object for creating a new user.
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=8)
```

Archivo: `backend_clean/src/application/dtos/token_dto.py`

```python
class TokenDTO(BaseModel):
    access_token: str = Field(...)
    refresh_token: str = Field(...)
    token_type: str = Field(default="bearer")
    expires_in: int = Field(default=3600)
```

### 15. Use Case de autenticacion

Archivo: `backend_clean/src/application/use_cases/authenticate_user_usecase.py`

```python
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
```

### 16. FastAPI endpoints de auth

Archivo: `backend_clean/src/presentation/api/endpoints/auth.py`

```python
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=ResponseDTO, status_code=status.HTTP_201_CREATED)
async def register(
    dto: CreateUserDTO,
    session: Session = Depends(get_db)
):
    """Register a new user."""
    user_repo = SQLAlchemyUserRepository(session)
    password_handler = PasswordHandler()
    
    use_case = CreateUserUseCase(user_repo, password_handler)
```

Login:

```python
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
```

### 17. FastAPI endpoints de tareas

Archivo: `backend_clean/src/presentation/api/endpoints/tasks.py`

```python
router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskDTO, status_code=status.HTTP_201_CREATED)
async def create_task(
    dto: CreateTaskDTO,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    task_repo = SQLAlchemyTaskRepository(session)
    use_case = CreateTaskUseCase(task_repo)
    return use_case.execute(dto, current_user.id)
```

### 18. Chatbot Flowi en frontend

Archivo: `frontend/src/App_auth.jsx`

```jsx
const [chatbotMessages, setChatbotMessages] = useState([
  { role: "bot", text: "¡Hola! Soy Flowi, tu asistente de TaskFlow. ¿En qué puedo ayudarte hoy?" }
]);
```

Encabezado:

```jsx
<h3>Flowi</h3>
<span>En línea</span>
```

Envio de mensajes:

```jsx
async function handleChatbotSubmit(event) {
  event.preventDefault();
  const userMessage = chatbotInput.trim();
  if (!userMessage || chatbotLoading) return;
  
  setChatbotMessages(prev => [...prev, { role: "user", text: userMessage }]);
  setChatbotInput("");
  setChatbotLoading(true);
  
  try {
    const accessToken = localStorage.getItem('tf_access_token');
    const response = await fetch("/chatbot", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ message: userMessage }),
    });
```

### 19. Chatbot Flowi en backend

Archivo: `backend/main.py`

```python
class ChatbotPayload(BaseModel):
    message: str

@app.post("/chatbot")
def chatbot(payload: ChatbotPayload, current_user: User = Depends(get_current_user)):
    user_message = payload.message.lower()
    original_message = payload.message
    username = current_user.username
    is_admin = current_user.is_admin
```

Memoria conversacional:

```python
session_id = f"chat_{username}"
if session_id not in chat_sessions:
    chat_sessions[session_id] = {"mode": "free", "pending_action": None}
session_state = chat_sessions[session_id]
```

### 20. 2FA

Campos.

Archivo: `backend/app/models.py`

```python
is_2fa_enabled: bool = Field(default=False)
totp_secret: Optional[str] = Field(default=None)
login_attempts: int = Field(default=0)
locked_until: Optional[datetime] = Field(default=None)
```

Setup.

Archivo: `backend/main.py`

```python
@app.post("/2fa/setup")
def setup_2fa(current_user: User = Depends(get_current_user)):
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA already enabled")
    
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    
    uri = totp.provisioning_uri(name=current_user.username, issuer_name="TaskFlow")
```

Login 2FA.

```python
@app.post("/login/2fa", response_model=Token)
def login_2fa(request: Request, payload: Verify2FAPayload):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == payload.username)).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.totp_secret:
            raise HTTPException(status_code=400, detail="2FA not configured for this user")
```

### 21. Admin y eliminacion de usuarios

Archivo: `backend/main.py`

```python
def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

Eliminar usuario:

```python
@app.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: User = Depends(require_admin)):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.username == current_user.username:
            raise HTTPException(status_code=400, detail="Admins cannot delete their own account")

        tasks = session.exec(select(Task).where(Task.owner == user.username)).all()
        for task in tasks:
            session.delete(task)
        session.delete(user)
        session.commit()
        return {"ok": True, "message": f"User {user.username} deleted"}
```

### 22. Subida de imagenes

Archivo: `backend/main.py`

```python
@app.post("/tasks/{task_id}/image")
async def upload_task_image(task_id: int, file: UploadFile, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        t = session.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if t.owner != current_user.username and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 5MB)")
```

Frontend:

Archivo: `frontend/src/App_auth.jsx`

```jsx
async function handleChatbotPhotoPick(file) {
  if (!file) return;

  setPendingChatImage(file);
  setChatbotMessages(prev => [...prev, {
    role: "user",
    text: `Foto seleccionada: ${file.name}`,
  }]);
```

### 23. pytest fixtures

Archivo: `backend_clean/tests/conftest.py`

```python
@pytest.fixture(scope="function")
def engine():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def db_session(SessionLocal):
    session = SessionLocal()
    yield session
    session.close()
```

### 24. BDD con Behave/Gherkin

Archivo: `backend_clean/tests/bdd/steps/user_steps.py`

```python
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

Archivo: `backend_clean/tests/bdd/features/user_registration.feature`

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
