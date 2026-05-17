# Asignado: Copilot
from fastapi import FastAPI, HTTPException, Depends, status, Request, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from sqlmodel import SQLModel, Field, create_engine, Session, select
from fastapi.responses import Response
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
import pyotp
import qrcode
import io
import base64
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI()

chat_sessions = {}

@app.get("/")
@app.get("/health")
def root():
    return {"status": "ok"}

SECRET_KEY = os.getenv("SECRET_KEY", "tu-super-secret-key-cambiala-en-produccion")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "refresh-secret-key-cambiala")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Asignado: Copilot — estado: in_progress
from app.db import engine
from app.models import User, Task

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

limiter = Limiter(key_func=get_remote_address)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    raise HTTPException(status_code=429, detail="Too many requests")

app.state.limiter = limiter

# CORS: allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5180", "http://localhost:5181", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5180", "http://127.0.0.1:5181", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Ensure DB tables exist
SQLModel.metadata.create_all(engine)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    owner: Optional[str] = None

class RegisterPayload(BaseModel):
    username: str
    password: str

class Verify2FAPayload(BaseModel):
    username: str
    code: str

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

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = verify_token(token, SECRET_KEY)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    username = payload.get("sub")
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def check_login_attempts(user: User):
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(status_code=423, detail="Account temporarily locked")
    if user.login_attempts >= 5:
        user.locked_until = datetime.utcnow() + timedelta(minutes=15)
        with Session(engine) as session:
            session.add(user)
            session.commit()
        raise HTTPException(status_code=423, detail="Too many login attempts. Locked for 15 minutes")

def reset_login_attempts(user: User):
    user.login_attempts = 0
    user.locked_until = None
    with Session(engine) as session:
        session.add(user)
        session.commit()

def increment_login_attempts(user: User):
    user.login_attempts += 1
    with Session(engine) as session:
        session.add(user)
        session.commit()

@app.post("/register")
def register(payload: RegisterPayload):
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == payload.username)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        user = User(username=payload.username, password_hash=hash_password(payload.password))
        session.add(user)
        session.commit()
        session.refresh(user)
        
        access_token = create_access_token({"sub": user.username})
        refresh_token = create_refresh_token({"sub": user.username})
        
        return {"id": user.id, "username": user.username, "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == form_data.username)).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(status_code=423, detail="Account temporarily locked")
        if not verify_password(form_data.password, user.password_hash):
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            session.add(user)
            session.commit()
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user.login_attempts = 0
        user.locked_until = None
        access_token = create_access_token({"sub": user.username})
        refresh_token = create_refresh_token({"sub": user.username})
        if user.is_2fa_enabled:
            session.commit()
            return Token(access_token="", refresh_token="", token_type="bearer")
        session.commit()
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


# Convenience JSON login endpoint for frontend (accepts JSON {username,password})
@app.post("/login_json", response_model=Token)
def login_json(payload: RegisterPayload):
    # Reuse same logic as form-based login
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == payload.username)).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(status_code=423, detail="Account temporarily locked")
        if not verify_password(payload.password, user.password_hash):
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            session.add(user)
            session.commit()
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user.login_attempts = 0
        user.locked_until = None
        access_token = create_access_token({"sub": user.username})
        refresh_token = create_refresh_token({"sub": user.username})
        session.commit()
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/admin/create_admin")
def create_admin(payload: RegisterPayload, x_admin_key: str = Header(None)):
    """Create an initial admin user. Requires ADMIN_SETUP_KEY env var and header 'X-Admin-Key'.
    This endpoint is intentionally gated and should only be used for initial setup.
    """
    setup_key = os.getenv("ADMIN_SETUP_KEY")
    if not setup_key:
        raise HTTPException(status_code=403, detail="Admin setup disabled")
    if x_admin_key != setup_key:
        raise HTTPException(status_code=401, detail="Invalid admin setup key")

    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == payload.username)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        user = User(username=payload.username, password_hash=hash_password(payload.password), is_admin=True, role="admin")
        session.add(user)
        session.commit()
        session.refresh(user)

        access_token = create_access_token({"sub": user.username})
        refresh_token = create_refresh_token({"sub": user.username})
        return {"id": user.id, "username": user.username, "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post("/login/2fa", response_model=Token)
def login_2fa(request: Request, payload: Verify2FAPayload):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == payload.username)).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.totp_secret:
            raise HTTPException(status_code=400, detail="2FA not configured for this user")
        
        try:
            code_str = str(payload.code).strip()
            totp = pyotp.TOTP(user.totp_secret)
            now_code = totp.now()
            is_valid = totp.verify(code_str, valid_window=1)
            
            # debug log removed
            
            if not is_valid:
                session.add(user)
                session.commit()
                raise HTTPException(status_code=401, detail="Invalid 2FA code")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"2FA error: {str(e)}")
        
        user.login_attempts = 0
        user.locked_until = None
        
        access_token = create_access_token({"sub": user.username})
        refresh_token = create_refresh_token({"sub": user.username})
        
        session.add(user)
        session.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

@app.post("/refresh", response_model=Token)
def refresh_token(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token, REFRESH_SECRET_KEY)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    username = payload.get("sub")
    access_token = create_access_token({"sub": username})
    refresh_token = create_refresh_token({"sub": username})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@app.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}

@app.post("/2fa/setup")
def setup_2fa(current_user: User = Depends(get_current_user)):
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA already enabled")
    
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    
    uri = totp.provisioning_uri(name=current_user.username, issuer_name="TaskFlow")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    current_user.totp_secret = secret
    with Session(engine) as session:
        session.add(current_user)
        session.commit()
    
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}"
    }

@app.post("/2fa/enable")
def enable_2fa(payload: Verify2FAPayload, current_user: User = Depends(get_current_user)):
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA already enabled")
    
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(payload.code):
        raise HTTPException(status_code=400, detail="Invalid code")
    
    current_user.is_2fa_enabled = True
    with Session(engine) as session:
        session.add(current_user)
        session.commit()
    
    return {"message": "2FA enabled successfully"}

@app.post("/2fa/disable")
def disable_2fa(payload: Verify2FAPayload, current_user: User = Depends(get_current_user)):
    if not current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA not enabled")
    
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(payload.code):
        raise HTTPException(status_code=400, detail="Invalid code")
    
    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    with Session(engine) as session:
        session.add(current_user)
        session.commit()
    
    return {"message": "2FA disabled successfully"}

@app.get("/users", response_model=List[dict])
def list_users(current_user: User = Depends(require_admin)):
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        return [{"id": u.id, "username": u.username, "is_admin": u.is_admin, "role": u.role, "is_2fa_enabled": u.is_2fa_enabled} for u in users]

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

@app.get("/users/{user_id}/tasks", response_model=List[Task])
def get_user_tasks_by_id(user_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        u = session.get(User, user_id)
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        tasks = session.exec(select(Task).where(Task.owner == u.username)).all()
        return tasks

@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate, current_user: User = Depends(get_current_user)):
    if not task.owner:
        task.owner = current_user.username
    
    if task.owner != current_user.username and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Cannot create task for another user")
    
    with Session(engine) as session:
        u = session.exec(select(User).where(User.username == task.owner)).first()
        if not u:
            raise HTTPException(status_code=400, detail="Owner user does not exist")
        t = Task(title=task.title, description=task.description, owner=task.owner)
        session.add(t)
        session.commit()
        session.refresh(t)
        return t

@app.get("/tasks", response_model=List[Task])
def list_tasks(current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        tasks = session.exec(select(Task)).all()
        return tasks

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        t = session.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        return t

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskCreate, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        t = session.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if t.owner != current_user.username and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        t.title = task.title
        t.description = task.description
        t.owner = task.owner
        session.add(t)
        session.commit()
        session.refresh(t)
        return t

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        t = session.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if t.owner != current_user.username and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        session.delete(t)
        session.commit()
        return {"ok": True}

@app.get("/tasks/by_status/{status}", response_model=List[Task])
def list_tasks_by_status(status: str, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        tasks = session.exec(select(Task).where(Task.status == status)).all()
        return tasks

@app.patch("/tasks/{task_id}/status", response_model=Task)
def change_task_status(task_id: int, status: str, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        t = session.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if t.owner != current_user.username and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        t.status = status
        session.add(t)
        session.commit()
        session.refresh(t)
        return t

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
        
        import base64
        image_data = base64.b64encode(contents).decode('utf-8')
        t.image = f"data:{file.content_type};base64,{image_data}"
        session.add(t)
        session.commit()
        session.refresh(t)
        return {"image": t.image}

@app.get("/tasks/{task_id}/image")
def get_task_image(task_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        t = session.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        if not t.image:
            raise HTTPException(status_code=404, detail="Image not found")
        # If stored as a data URI (data:<media_type>;base64,<data>), decode and return binary
        if isinstance(t.image, str) and t.image.startswith("data:"):
            try:
                header, b64 = t.image.split(',', 1)
                media_type = header.split(';')[0].split(':', 1)[1]
                import base64
                data = base64.b64decode(b64)
                return Response(content=data, media_type=media_type)
            except Exception:
                raise HTTPException(status_code=500, detail="Invalid image data")
        # Fallback: return JSON (backwards compatibility)
        return {"image": t.image}

@app.get("/tasks/by_user/{username}", response_model=List[Task])
def list_tasks_by_user(username: str, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        tasks = session.exec(select(Task).where(Task.owner == username)).all()
        return tasks

@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "role": current_user.role,
        "is_2fa_enabled": current_user.is_2fa_enabled
    }

@app.post("/admin/promote/{username}")
def promote_user(username: str, current_user: User = Depends(require_admin)):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_admin = True
        user.role = "admin"
        session.add(user)
        session.commit()
        return {"message": f"User {username} promoted to admin"}

@app.post("/admin/demote/{username}")
def demote_user(username: str, current_user: User = Depends(require_admin)):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.username == current_user.username:
            raise HTTPException(status_code=400, detail="Cannot demote yourself")
        user.is_admin = False
        user.role = "user"
        session.add(user)
        session.commit()
        return {"message": f"User {username} demoted to user"}


# Public endpoints for development/backwards-compatibility (no auth)
@app.get('/public/tasks', response_model=List[Task])
def public_list_tasks():
    with Session(engine) as session:
        return session.exec(select(Task)).all()

@app.post('/public/tasks', response_model=Task)
def public_create_task(task: TaskCreate):
    with Session(engine) as session:
        t = Task(title=task.title, description=task.description, owner=task.owner)
        session.add(t)
        session.commit()
        session.refresh(t)
        return t

@app.post('/public/register')
def public_register(payload: RegisterPayload):
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == payload.username)).first()
        if existing:
            raise HTTPException(status_code=400, detail='Username already exists')
        user = User(username=payload.username, password_hash=hash_password(payload.password))
        session.add(user)
        session.commit()
        session.refresh(user)
        return {'id': user.id, 'username': user.username}

class ChatbotPayload(BaseModel):
    message: str

def parse_task_command(message: str, username: str, action: str):
    import re
    if action == "crear":
        title_match = re.search(r'(?:crea|créate|nueva|nuevo|hacer)[:\s]+(.+)', message, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            desc_match = re.search(r'descripci[óo]n[:\s]+(.+)', message, re.IGNORECASE)
            description = desc_match.group(1).strip() if desc_match else ""
            return {"action": "create", "title": title, "description": description}
    elif action in ["hacer", "completar", "terminar"]:
        return {"action": "complete_task", "message": message}
    elif action in ["eliminar", "borrar", "borre"]:
        return {"action": "delete_task", "message": message}
    elif action in ["ver", "mostrar", "lista"]:
        return {"action": "list_tasks"}
    elif action in ["estado", "cambiar"]:
        return {"action": "change_status", "message": message}
    return None

@app.post("/chatbot")
def chatbot(payload: ChatbotPayload, current_user: User = Depends(get_current_user)):
    user_message = payload.message.lower()
    original_message = payload.message
    username = current_user.username
    is_admin = current_user.is_admin
    
    import re

    session_id = f"chat_{username}"
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {"mode": "free", "pending_action": None}
    session_state = chat_sessions[session_id]

    def clear_pending_chat_action():
        session_state["mode"] = "free"
        session_state["pending_action"] = None
        session_state.pop("selected_task", None)

    def find_task_by_reference(session: Session, text: str) -> Optional[Task]:
        reference = text.strip()
        id_match = re.search(r'#?\b(\d+)\b', reference)
        if id_match:
            task = session.get(Task, int(id_match.group(1)))
            if task and (task.owner == username or is_admin):
                return task

        cleaned = re.sub(
            r'^(?:la\s+)?(?:tarea\s+)?(?:de\s+)?(?:la\s+de\s+)?(?:foto\s+de\s+)?(?:imagen\s+de\s+)?',
            '',
            reference,
            flags=re.IGNORECASE,
        ).strip(" .,!?:;\"'")
        if not cleaned:
            return None

        owned_tasks = session.exec(select(Task).where(Task.owner == username)).all()
        if is_admin:
            owned_tasks = session.exec(select(Task)).all()

        cleaned_lower = cleaned.lower()
        for task in owned_tasks:
            if task.title.lower() == cleaned_lower:
                return task
        for task in owned_tasks:
            title_lower = task.title.lower()
            if cleaned_lower in title_lower or title_lower in cleaned_lower:
                return task
        return None

    def photo_upload_response(task: Task):
        clear_pending_chat_action()
        return {
            "response": f"📷 Para agregar foto a '{task.title}':\n\n1. Abre la tarea en la app\n2. Click en 'Subir imagen'\n3. Selecciona la foto\n\nO usa la API: POST /tasks/{task.id}/image con un archivo JPEG/PNG",
            "action": "photo_upload",
            "task_id": task.id,
        }

    def clean_task_title(raw_title: str) -> str:
        title = raw_title.strip().strip('"').strip("'").strip()
        title = re.sub(
            r'^(?:crea(?:r)?|creame|créame|hazme|hacer|agrega(?:r)?|agregame|agrégame|nueva|nuevo|anota|anotame|anótame|pon|ponerme)\s+',
            '',
            title,
            flags=re.IGNORECASE,
        ).strip()
        title = re.sub(
            r'^(?:una\s+|un\s+)?(?:tarea\s+)?(?:que\s+)?(?:se\s+)?(?:llame|llamada|llamado|nombre|titulada|titulado|con\s+nombre)\s+',
            '',
            title,
            flags=re.IGNORECASE,
        ).strip()
        title = re.sub(r'^(?:una\s+|un\s+)?tarea\s+', '', title, flags=re.IGNORECASE).strip()
        return title.strip('"').strip("'").strip()

    def update_pending_task_description(description: str):
        task_id = session_state.get("selected_task")
        if not task_id:
            clear_pending_chat_action()
            return {"response": "Perdí la referencia de la tarea. Dime el ID o vuelve a abrir la tarea."}

        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task or (task.owner != username and not is_admin):
                clear_pending_chat_action()
                return {"response": "No encontré esa tarea o no tienes permiso para modificarla."}

            task.description = description.strip()
            session.add(task)
            session.commit()
            clear_pending_chat_action()
            return {
                "response": f"✅ Descripción agregada a '{task.title}'\n📝 {task.description}",
                "action": "task_updated",
                "task_id": task.id,
            }

    yes_words = {"si", "sí", "s", "yes", "y", "claro", "dale", "ok", "okay", "vale", "hazlo"}
    no_words = {"no", "n", "nop", "nope", "cancelar", "cancela", "dejalo", "déjalo"}
    desc_request = re.search(r'(?:ponle|agrega|añade|anade|coloca|poner|agregar|añadir|anadir)\s+(?:una\s+)?descripci[óo]n(?:\s*[:\-]\s*(.+))?$', original_message, re.IGNORECASE)

    if session_state.get("pending_action") in {"ask_description", "await_description"}:
        cleaned = user_message.strip()
        desc_text = desc_request.group(1).strip() if desc_request and desc_request.group(1) else ""

        if cleaned in no_words:
            clear_pending_chat_action()
            return {"response": "Perfecto, la dejo sin descripción. ¿Algo más?"}

        if session_state["pending_action"] == "ask_description":
            if cleaned in yes_words or desc_request:
                session_state["pending_action"] = "await_description"
                if desc_text:
                    return update_pending_task_description(desc_text)
                return {"response": "Listo. Escríbeme la descripción que quieres guardar."}

            if len(original_message.strip()) >= 3:
                return update_pending_task_description(original_message)

        if session_state["pending_action"] == "await_description":
            if desc_request and not desc_text:
                return {"response": "Dime el texto de la descripción. Ej: 'comprar pan y leche antes de las 6'."}
            return update_pending_task_description(desc_text or original_message)

    if session_state.get("pending_action") == "photo":
        if user_message.strip() in no_words:
            clear_pending_chat_action()
            return {"response": "Ok, cancelé lo de la foto. ¿Qué más necesitas?"}

        with Session(engine) as session:
            task = find_task_by_reference(session, original_message)
            if task:
                return photo_upload_response(task)
        return {"response": "No encontré esa tarea. Dame el ID o escribe el nombre más parecido. Ej: `#14` o `Prueba5`."}
    
    # ==================== PRIORIDAD 1: FOTO/IMAGEN ====================
    # "agregar foto a", "subir imagen", "ponle foto", "mándame la foto", etc
    foto_palabras = ["foto", "imagen", "subir foto", "agregar foto", "agregar imagen", "ponle foto", "sube una foto", "mándame", "mandame una foto", "foto de", "imagen de", "photo", "picture", "attachment"]
    foto_accion = any(p in user_message for p in foto_palabras)
    if foto_accion:
        task_id_match = re.search(r'#(\d+)', user_message)
        task_name_match = re.search(r'(?:foto|imagen|photo|picture)\s+(?:de|a|para|la|del)\s+(?:tarea\s+)?(.+?)(?:$|\.|,|!|y\s|$)', original_message, re.IGNORECASE)
        
        # Buscar tarea específica o más reciente
        with Session(engine) as session:
            task = None
            if task_id_match:
                task = session.get(Task, int(task_id_match.group(1)))
            elif task_name_match:
                search = task_name_match.group(1).strip()
                if len(search) > 0:
                    task = find_task_by_reference(session, search)
            
            if task:
                return photo_upload_response(task)
            elif task_id_match:
                return {"response": f"❌ No encontré tarea con ID #{task_id_match.group(1)}"}
            else:
                session_state["mode"] = "awaiting_task_reference"
                session_state["pending_action"] = "photo"
                return {"response": "¿A cuál tarea quieres agregar la foto? Dame el nombre o ID.\nEj: 'foto de comprar leche' o 'foto #1'"}
    
    # ==================== PRIORIDAD 2: COMPLETAR TAREA ====================
    completar_palabras = ["ya la", "ya lo", "ya está", "ya esta", "ya terminé", "ya termine", "ya hice", "ya completé", "ya complete", "listo", "hecho", "done", "completado", "completada", "terminado", "terminada", "marcada", "marcado", "marcar como", "marcala", "marcarlo", "ponele", "ponla", "ya", "check", "✓", "x", "completa"]
    if any(p in user_message for p in completar_palabras):
        id_match = re.search(r'#(\d+)', user_message)
        name_match = re.search(r'(?:la|lo|que|con|de|del|para)\s+(?:tarea\s+)?(.+?)(?:$|\.|,|!|y\s|$)', original_message, re.IGNORECASE)
        
        with Session(engine) as session:
            task = None
            if id_match:
                task = session.get(Task, int(id_match.group(1)))
            elif name_match:
                search = name_match.group(1).strip()
                if len(search) > 0:
                    task = session.exec(select(Task).where(Task.title.ilike(f"%{search}%"), Task.owner == username)).first()
            
            if task:
                if task.owner != username and not is_admin:
                    return {"response": "❌ No tienes permiso para modificar esta tarea"}
                task.status = "done"
                session.add(task)
                session.commit()
                return {"response": f"✅ ¡'{task.title}' completada! 🎉\n🆔 ID: #{task.id}\n¡Sigue así!", "action": "task_completed"}
            elif id_match:
                return {"response": f"❌ No encontré tarea con ID #{id_match.group(1)}"}
            else:
                return {"response": "❌ ¿Cuál tarea completaste? Dame el nombre o ID."}
    
    # ==================== PRIORIDAD 3: ELIMINAR TAREA ====================
    eliminar_palabras = ["borra", "borrar", "borre", "elimina", "eliminar", "elimine", "quitar", "quitala", "quitame", "sacame", "sacar", "delete", "remover", "ya no necesito", "ya no quiero", "deshazte", "elimina la"]
    if any(p in user_message for p in eliminar_palabras):
        id_match = re.search(r'#(\d+)', user_message)
        name_match = re.search(r'(?:la|lo|que|de|del|para)\s+(?:tarea\s+)?(.+?)(?:$|\.|,|!|y\s)', original_message, re.IGNORECASE)
        
        with Session(engine) as session:
            task = None
            if id_match:
                task = session.get(Task, int(id_match.group(1)))
            elif name_match:
                search = name_match.group(1).strip()
                if len(search) > 0:
                    task = session.exec(select(Task).where(Task.title.ilike(f"%{search}%"), Task.owner == username)).first()
            
            if task:
                if task.owner != username and not is_admin:
                    return {"response": "❌ No tienes permiso para eliminar esta tarea"}
                task_title = task.title
                session.delete(task)
                session.commit()
                return {"response": f"🗑️ '{task_title}' eliminada.\n¿Algo más?", "action": "task_deleted"}
            elif id_match:
                return {"response": f"❌ No encontré tarea con ID #{id_match.group(1)}"}
            else:
                return {"response": "❌ ¿Cuál tarea eliminas? Dame el nombre o ID."}
    
    # ==================== PRIORIDAD 4: VER TAREAS ====================
    ver_palabras = ["mis tareas", "ver tareas", "mostrar tareas", "lista", "qué tareas tengo", "tareas mías", "mis pendientes", "qué tengo", "que tengo", "cuántas tareas", "cuantas tareas", "dame mis", "muestrame", "muéstrame", "dime qué", "dime que", "enséñame", "las tareas", "tareas pendientes", "tareas activas", "show", "list"]
    if any(w in user_message for w in ver_palabras):
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.owner == username)).all()
            if not tasks:
                return {"response": "📭 No tienes tareas. Solo dime 'crea [nombre]' y la creo."}
            
            pending = [t for t in tasks if t.status == "todo"]
            in_progress = [t for t in tasks if t.status == "in_progress"]
            done = [t for t in tasks if t.status == "done"]
            
            response = f"📋 TUS TAREAS (Total: {len(tasks)})\n"
            response += f"⏳{len(pending)} | 🔄{len(in_progress)} | ✅{len(done)}\n\n"
            
            if pending:
                for t in pending[:10]:
                    response += f"#{t.id} • {t.title}\n"
            if len(pending) > 10:
                response += f"...y {len(pending)-10} más\n"
            
            if in_progress:
                response += "\n🔄 EN REVISIÓN:\n"
                for t in in_progress[:5]:
                    response += f"#{t.id} • {t.title}\n"
            
            if done:
                response += "\n✅ COMPLETADAS:\n"
                for t in done[:5]:
                    response += f"#{t.id} • {t.title}\n"
            
            return {"response": response}
    
    # ==================== PRIORIDAD 5: EN REVISIÓN ====================
    revision_palabras = ["en revisión", "en revision", "revisión", "revisar", "review", "revisa", "pon en revision", "ponle en revision", "pending", "working on", "working"]
    if any(p in user_message for p in revision_palabras):
        id_match = re.search(r'#(\d+)', user_message)
        name_match = re.search(r'(?:la|lo|que|de|del|para)\s+(?:tarea\s+)?(.+?)(?:$|\.|,|!|y\s)', original_message, re.IGNORECASE)
        
        with Session(engine) as session:
            task = None
            if id_match:
                task = session.get(Task, int(id_match.group(1)))
            elif name_match:
                search = name_match.group(1).strip()
                if len(search) > 0:
                    task = session.exec(select(Task).where(Task.title.ilike(f"%{search}%"), Task.owner == username)).first()
            
            if task and (task.owner == username or is_admin):
                task.status = "in_progress"
                session.add(task)
                session.commit()
                return {"response": f"🔄 '{task.title}' en revisión.\n🆔 ID: #{task.id}", "action": "task_updated"}
            elif id_match:
                return {"response": f"❌ No encontré tarea #{id_match.group(1)}"}
            else:
                return {"response": "❌ ¿Cuál tarea pones en revisión?"}
    
    # ==================== PRIORIDAD 6: PENDIENTE ====================
    pendiente_palabras = ["pendiente", "por hacer", "todo", "back to", "vuelve a", "sin hacer", "hacer"]
    if any(p in user_message for p in pendiente_palabras):
        id_match = re.search(r'#(\d+)', user_message)
        name_match = re.search(r'(?:la|lo|que|de|del|para)\s+(?:tarea\s+)?(.+?)(?:$|\.|,|!|y\s)', original_message, re.IGNORECASE)
        
        with Session(engine) as session:
            task = None
            if id_match:
                task = session.get(Task, int(id_match.group(1)))
            elif name_match:
                search = name_match.group(1).strip()
                if len(search) > 0:
                    task = session.exec(select(Task).where(Task.title.ilike(f"%{search}%"), Task.owner == username)).first()
            
            if task and (task.owner == username or is_admin):
                task.status = "todo"
                session.add(task)
                session.commit()
                return {"response": f"⏳ '{task.title}' marcada como pendiente.\n🆔 ID: #{task.id}", "action": "task_updated"}
            elif id_match:
                return {"response": f"❌ No encontré tarea #{id_match.group(1)}"}
            else:
                return {"response": "❌ ¿Cuál tarea pones pendiente?"}
    
    # ==================== PRIORIDAD 7: BUSCAR ====================
    buscar_palabras = ["busca", "buscar", "busca tarea", "encuentra", "search", "find", "dónde está", "donde esta", "busca"]
    if any(p in user_message for p in buscar_palabras):
        search_match = re.search(r'(?:busca|buscar|encuentra|search)[:\s]+(.+)', original_message, re.IGNORECASE)
        if search_match:
            search_term = search_match.group(1).strip()
            with Session(engine) as session:
                tasks = session.exec(select(Task).where(Task.owner == username, Task.title.ilike(f"%{search_term}%"))).all()
                if not tasks:
                    return {"response": f"🔍 No hay tareas con '{search_term}'."}
                
                response = f"🔍 RESULTADOS ({len(tasks)}):\n"
                for t in tasks[:10]:
                    status = "⏳" if t.status == "todo" else "🔄" if t.status == "in_progress" else "✅"
                    response += f"{status} #{t.id} • {t.title}\n"
                return {"response": response}
    
    # ==================== PRIORIDAD 8: ESTADÍSTICAS/STATS ====================
    stats_palabras = ["estadísticas", "stats", "resumen", "informe", "progreso", "cómo voy", "mi progreso", "avance", "summary", "informe", "progress"]
    if any(w in user_message for w in stats_palabras):
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.owner == username)).all()
            if not tasks:
                return {"response": "📊 No tienes tareas aún."}
            
            total = len(tasks)
            done = len([t for t in tasks if t.status == "done"])
            pending = len([t for t in tasks if t.status == "todo"])
            pct = (done / total * 100) if total > 0 else 0
            
            response = f"📊 ESTADÍSTICAS DE {username}\n"
            response += f"═" * 20 + "\n"
            response += f"Completadas: {done}/{total} ({pct:.0f}%)\n"
            response += f"Pendientes: {pending}\n"
            if pct >= 80:
                response += "\n🎉 ¡Excelente!"
            elif pct >= 50:
                response += "\n💪 ¡Vas bien!"
            else:
                response += "\n🚀 ¡A trabajar!"
        # Buscar título después de las palabras clave
        title = ""
        desc = ""
        
        # Patrón: "crea una tarea [titulo] con descripción [desc]" o "crea [titulo] - [desc]"
        patterns = [
            r'(?:crea|crear|creame|hazme|hacer|agrega|agregame|nueva|nuevo|anota|anotame|pon|ponerme|no olvidar|recuerdame)[:\s]+(?:una\s+)?(?:tarea\s+)?(?:que\s+)?(?:llamada\s+)?(?:para\s+)?(?:llam\s+)?["\']?([^"\']+(?:["\'][^"\']+["\'])?)',
            r'(?:crea|crear|creame|hazme|hacer|agrega|agregame|nueva|nuevo|anota|anotame|pon|ponerme)[:\s]+(?:una\s+)?(?:tarea\s+)?["\']?([^"\']+)["\']?',
            r'(?:crea|crear|creame|hazme|hacer|agrega|agregame|nueva|nuevo|anota|anotame|pon|ponerme)[:\s]+(.+)',
            r'^(?:crea|crear|creame|hazme|hacer|agrega|agregame|nueva|nuevo|anota|anotame|pon|ponerme)\s+(.+)$',
            r'["\']?([^"\']+(?:["\'][^"\']+)?)["\']?\s*(?:y\s+)?(?:con\s+)?(?:descripci[óo]n\s*[:\-]?\s*|para\s+)?(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, original_message, re.IGNORECASE)
            if match and len(match.group(1).strip()) > 1:
                potential_title = clean_task_title(match.group(1))
                # Si tiene "con descripción" o "para", separar
                if 'con descripción' in potential_title.lower() or 'con descripcion' in potential_title.lower():
                    parts = re.split(r'\s+(?:con\s+descripci[óo]n|con\s+descripcion)\s*[:\-]?\s*', potential_title, maxsplit=1)
                    title = parts[0].strip()
                    desc = parts[1].strip() if len(parts) > 1 else ""
                elif 'para' in potential_title.lower() and potential_title.lower().index('para') > 3:
                    parts = re.split(r'\s+para\s+', potential_title, maxsplit=1)
                    title = parts[0].strip()
                    desc = parts[1].strip() if len(parts) > 1 else ""
                else:
                    # Tratar como título nomás
                    title = potential_title
                break
        
        if not title:
            # Extraer lo que queda como título
            for kw in crear_palabras:
                if kw in user_message:
                    idx = user_message.index(kw)
                    rest = original_message[idx:].strip()
                    for char in ['crea', 'crear', 'hazme', 'hacer', 'agrega', 'agregar', 'nueva', 'nuevo', 'anota', 'anotame', 'pon', 'no']:
                        if rest.lower().startswith(char):
                            rest = rest[len(char):].strip()
                    title = clean_task_title(rest)
                    break
        
        # Buscar descripción separada
        desc_match = re.search(r'(?:descripci[óo]n|descripcion|descripciòn|descripci?n)[:\s]+(.+?)(?:$|(?:y\s+)|(?:\.|,|$))', original_message, re.IGNORECASE)
        if desc_match:
            desc = desc_match.group(1).strip()
        elif not desc:
            # Buscar después del título con "y" o ","
            parts_match = re.search(r'(?:["\']|y\s+|,\s*)(.+?)(?:$|\.|\?|!|$)', original_message)
            if parts_match and len(parts_match.group(1)) > 5:
                possible_desc = parts_match.group(1).strip()
                if possible_desc != title and len(possible_desc) > 2:
                    desc = possible_desc
        
        # Limpiar título de palabras residuals
        title = clean_task_title(title)
        title = re.sub(r'^(?:que\s+)?(?:se\s+)?(?:llame\s+)?(?:como\s+)?', '', title, flags=re.IGNORECASE).strip()
        title = re.sub(r'(?:es\s+)?(?:para\s+)?(?:hacer\s+)?$', '', title, flags=re.IGNORECASE).strip()
        
        if title and len(title) > 0 and len(title) < 200:
            with Session(engine) as session:
                t = Task(title=title, description=desc or "", owner=username)
                session.add(t)
                session.commit()
                session.refresh(t)
                return {"response": f"✅ Tarea creada: '{t.title}'\n📝 Descripción: {desc or 'Sin descripción'}\n🆔 ID: #{t.id}\n\n¿Algo más?", "action": "task_created", "task_id": t.id}
    
    # ==================== SALUDOS ====================
            
            pct_done = (done / total * 100) if total > 0 else 0
            
            response = f"📊 ESTADÍSTICAS DE {username}\n"
            response += "═" * 25 + "\n"
            response += f"📈 Progreso: {pct_done:.1f}%\n"
            response += f"⏳ Pendientes: {pending}\n"
            response += f"🔄 En revisión: {in_progress}\n"
            response += f"✅ Completadas: {done}\n"
            response += f"📋 Total: {total}\n"
            
            if pct_done >= 80:
                response += "\n🎉 ¡Excelente trabajo! ¡Casi completas todas tus tareas!"
            elif pct_done >= 50:
                response += "\n💪 ¡Vas bien! ¡Sigue así!"
            else:
                response += "\n🚀 ¡Aun hay trabajo por hacer!"
            
            return {"response": response}
    
    # ==================== COMPLETAR TAREA - LENGUAJE NATURAL ====================
    # "ya la hice", "ya está", "listo", "terminado", "completado", "done", "marcala como", "ya completé", etc
    completar_palabras = ["ya la", "ya lo", "ya está", "ya esta", "ya terminé", "ya termine", "ya hice", "ya hice la", "ya completé", "ya complete", "listo", "listo con", "listo la", "hecho", "hecho con", "done", "done with", "completado", "completada", "terminado", "terminada", "marcada", "marcado", "marcar como", "marcala", "marcarlo", "ponele", "ponla", "ya", "check", "✓", "x"]
    if any(p in user_message for p in completar_palabras):
        # Buscar ID o nombre
        id_match = re.search(r'#(\d+)', user_message)
        name_match = re.search(r'(?:la|lo|que|con|de|del|para)\s+(?:tarea\s+)?(.+?)(?:$|\.|,|!|$|(?:y\s)|(?:\s+y))', original_message, re.IGNORECASE)
        
        with Session(engine) as session:
            task = None
            if id_match:
                task_id = int(id_match.group(1))
                task = session.get(Task, task_id)
            elif name_match:
                search = name_match.group(1).strip()
                if len(search) > 0:
                    task = session.exec(select(Task).where(Task.title.ilike(f"%{search}%"), Task.owner == username)).first()
            
            if task:
                if task.owner != username and not is_admin:
                    return {"response": "❌ No tienes permiso para modificar esta tarea"}
                task.status = "done"
                session.add(task)
                session.commit()
                return {"response": f"✅ ¡Tarea '{task.title}' completada! 🎉\n🆔 ID: #{task.id}\n¡Sigue así!", "action": "task_completed"}
            elif id_match:
                return {"response": f"❌ No encontré tarea con ID #{id_match.group(1)}"}
            else:
                return {"response": "❌ ¿Cuál tarea quieres completar? Dame el nombre o ID.\nEj: 'ya la tarea 1' o 'ya está comprar leche'"}
    
    # ==================== ELIMINAR TAREA - LENGUAJE NATURAL ====================
    # "borra", "elimina", "quitar", "delete", "sacame", "quitame", "ya no necesito", etc
    eliminar_palabras = ["borra", "borrar", "borre", "elimina", "eliminar", "elimine", "quitar", "quitala", "quitame", "sacame", "sacar", "delete", "del", "remover", "ya no necesito", "ya no quiero", "ya no", "bárramelo", "deshazte"]
    if any(p in user_message for p in eliminar_palabras):
        id_match = re.search(r'#(\d+)', user_message)
        name_match = re.search(r'(?:la|lo|que|de|del|para)\s+(?:tarea\s+)?(.+?)(?:$|\.|,|!|y\s)', original_message, re.IGNORECASE)
        
        with Session(engine) as session:
            task = None
            if id_match:
                task_id = int(id_match.group(1))
                task = session.get(Task, task_id)
            elif name_match:
                search = name_match.group(1).strip()
                if len(search) > 0:
                    task = session.exec(select(Task).where(Task.title.ilike(f"%{search}%"), Task.owner == username)).first()
            
            if task:
                if task.owner != username and not is_admin:
                    return {"response": "❌ No tienes permiso para eliminar esta tarea"}
                task_title = task.title
                session.delete(task)
                session.commit()
                return {"response": f"🗑️ Tarea '{task_title}' eliminada.\n\n¿Algo más?", "action": "task_deleted"}
            elif id_match:
                return {"response": f"❌ No encontré tarea con ID #{id_match.group(1)}"}
            else:
                return {"response": "❌ ¿Cuál tarea quieres eliminar? Dame el nombre o ID.\nEj: 'elimina la tarea 1' o 'borra comprar leche'"}
    
    # ==================== EN REVISIÓN ====================
    if any(w in user_message for w in ["pon en revisión", "en revisión", "revisión", "revisar", "review", "审核"]):
        task_id_match = re.search(r'#?(\d+)', user_message)
        title_match = re.search(r'(?:en revisión|revisar)[:\s]+"?(.+?)"?$', original_message, re.IGNORECASE)
        
        if task_id_match:
            task_id = int(task_id_match.group(1))
        elif title_match:
            title_search = title_match.group(1).strip()
            with Session(engine) as session:
                task = session.exec(select(Task).where(Task.title.ilike(f"%{title_search}%"), Task.owner == username)).first()
                if task:
                    task_id = task.id
                else:
                    return {"response": f"❌ No encontré tarea con '{title_search}'."}
        else:
            return {"response": "📝 Especifica qué tarea poner en revisión:\n• 'en revisión #1' (por ID)\n• 'en revisión [nombre]'"}

        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return {"response": f"❌ No encontré tarea con ID #{task_id}"}
            
            task.status = "in_progress"
            session.add(task)
            session.commit()
            return {"response": f"🔄 Tarea '{task.title}' puesta en revisión.\n🆔 ID: #{task.id}\n\n¿Algo más?", "action": "task_updated"}
    
    # ==================== PENDIENTE ====================
    if any(w in user_message for w in ["pendiente", "por hacer", "todo", "back to todo"]):
        task_id_match = re.search(r'#?(\d+)', user_message)
        title_match = re.search(r'(?:pendiente|por hacer)[:\s]+"?(.+?)"?$', original_message, re.IGNORECASE)
        
        if task_id_match:
            task_id = int(task_id_match.group(1))
        elif title_match:
            title_search = title_match.group(1).strip()
            with Session(engine) as session:
                task = session.exec(select(Task).where(Task.title.ilike(f"%{title_search}%"), Task.owner == username)).first()
                if task:
                    task_id = task.id
                else:
                    return {"response": f"❌ No encontré tarea con '{title_search}'."}
        else:
            return {"response": "📝 Especifica qué tarea poner pendiente:\n• 'pendiente #1' (por ID)\n• 'pendiente [nombre]'"}
        
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return {"response": f"❌ No encontré tarea con ID #{task_id}"}
            
            task.status = "todo"
            session.add(task)
            session.commit()
            return {"response": f"⏳ Tarea '{task.title}' marcada como pendiente.\n🆔 ID: #{task.id}\n\n¿Algo más?", "action": "task_updated"}
    
    # ==================== BUSCAR TAREA ====================
    if any(w in user_message for w in ["busca", "buscar", "busca tarea", "encuentra", "search", "find"]):
        search_match = re.search(r'(?:busca|buscar|encuentra|search)[:\s]+(.+)', original_message, re.IGNORECASE)
        if search_match:
            search_term = search_match.group(1).strip()
            with Session(engine) as session:
                tasks = session.exec(select(Task).where(Task.owner == username, Task.title.ilike(f"%{search_term}%"))).all()
                if not tasks:
                    return {"response": f"🔍 No encontré tareas que contengan '{search_term}'."}
                
                response = f"🔍 RESULTADOS PARA '{search_term}':\n"
                for t in tasks:
                    status_icon = "⏳" if t.status == "todo" else "🔄" if t.status == "in_progress" else "✅"
                    response += f"{status_icon} #{t.id} • {t.title}\n"
                    if t.description:
                        response += f"   📝 {t.description[:50]}...\n"
                return {"response": response}
    
    # ==================== VER TAREA DETALLE ====================
    if any(w in user_message for w in ["detalle", "info", "ver detalle", "muestra", "show", "details"]):
        task_id_match = re.search(r'#?(\d+)', user_message)
        if task_id_match:
            task_id = int(task_id_match.group(1))
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if not task:
                    return {"response": f"❌ No encontré tarea con ID #{task_id}"}
                
                status_text = {"todo": "⏳ Pendiente", "in_progress": "🔄 En Revisión", "done": "✅ Completada"}
                response = f"📋 DETALLE DE TAREA\n"
                response += "═" * 20 + "\n"
                response += f"🆔 ID: #{task.id}\n"
                response += f"📌 Título: {task.title}\n"
                response += f"📝 Descripción: {task.description or 'Sin descripción'}\n"
                response += f"📌 Estado: {status_text.get(task.status, task.status)}\n"
                response += f"👤 Propietario: {task.owner}\n"
                return {"response": response}
    
    # ==================== ACTUALIZAR DESCRIPCIÓN ====================
    if any(w in user_message for w in ["actualiza", "actualizar", "cambia descripcion", "cambia descripción", "update desc"]):
        update_match = re.search(r'#(\d+)[:\s]+(.+)', original_message, re.IGNORECASE)
        if update_match:
            task_id = int(update_match.group(1))
            new_desc = update_match.group(2).strip()
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if not task:
                    return {"response": f"❌ No encontré tarea con ID #{task_id}"}
                if task.owner != username and not is_admin:
                    return {"response": "❌ No tienes permiso para modificar esta tarea"}
                
                task.description = new_desc
                session.add(task)
                session.commit()
                return {"response": f"✅ Descripción actualizada para '{task.title}'\n📝 Nueva descripción: {new_desc}"}
    
    # ==================== VER TODAS LAS TAREAS (ADMIN) ====================
    if any(w in user_message for w in ["todas las tareas", "todas tareas", "all tasks", "ver todas"]) and is_admin:
        with Session(engine) as session:
            tasks = session.exec(select(Task)).all()
            if not tasks:
                return {"response": "📭 No hay tareas en el sistema."}
            
            response = f"📋 TODAS LAS TAREAS ({len(tasks)})\n"
            response += "═" * 30 + "\n"
            for t in tasks[:20]:
                status_icon = "⏳" if t.status == "todo" else "🔄" if t.status == "in_progress" else "✅"
                response += f"{status_icon} #{t.id} | {t.owner}: {t.title}\n"
            
            if len(tasks) > 20:
                response += f"\n... y {len(tasks) - 20} más"
            return {"response": response}
    
    # ==================== VER USUARIOS (ADMIN) ====================
    if any(w in user_message for w in ["usuarios", "users", "lista usuarios", "ver usuarios"]) and is_admin:
        with Session(engine) as session:
            users = session.exec(select(User)).all()
            response = f"👥 USUARIOS DEL SISTEMA ({len(users)})\n"
            response += "═" * 25 + "\n"
            for u in users:
                admin_badge = " 🔧" if u.is_admin else ""
                response += f"• {u.username}{admin_badge}\n"
            return {"response": response}
    
    # Si estamos esperando selección de tarea
    if session_state.get("pending_action"):
        action = session_state["pending_action"]
        
        # Verificar si es un número de tarea
        num_match = re.match(r'^(\d+)$', user_message.strip())
        if num_match:
            task_num = int(num_match.group(1))
            with Session(engine) as session:
                tasks = session.exec(select(Task).where(Task.owner == username, Task.status != "done")).all()
                if 1 <= task_num <= len(tasks):
                    task = tasks[task_num - 1]
                    
                    if action == "status":
                        # Mostrar opciones de estado
                        session_state["mode"] = "select_status"
                        session_state["selected_task"] = task.id
                        return {"response": f"📋 Tarea: '{task.title}'\n\nSelecciona nuevo estado:\n1️⃣ Pendiente\n2️⃣ En revisión\n3️⃣ Completada", "pending_action": "finalize_status"}
                    elif action == "photo":
                        session_state["mode"] = "free"
                        session_state["pending_action"] = None
                        return {"response": f"📷 Para agregar foto a '{task.title}':\n\n1. Abre la tarea en la app\n2. Click en 'Subir imagen'\n3. Selecciona la foto\n\nO usa: POST /tasks/{task.id}/image", "action": "photo_upload", "task_id": task.id}
                    elif action == "complete":
                        task.status = "done"
                        session.add(task)
                        session.commit()
                        session_state["mode"] = "free"
                        session_state["pending_action"] = None
                        return {"response": f"✅ ¡'{task.title}' completada! 🎉\n🆔 ID: #{task.id}", "action": "task_completed"}
                    elif action == "delete":
                        task_title = task.title
                        session.delete(task)
                        session.commit()
                        session_state["mode"] = "free"
                        session_state["pending_action"] = None
                        return {"response": f"🗑️ '{task_title}' eliminada.", "action": "task_deleted"}
                    elif action == "edit":
                        session_state["mode"] = "edit_title"
                        session_state["selected_task"] = task.id
                        return {"response": f"✏️ Tarea: '{task.title}'\n\nEscribe el nuevo nombre para la tarea:"}
        
        # Si seleccionó estado
        if session_state.get("mode") == "select_status":
            status_map = {"1": "todo", "2": "in_progress", "3": "done"}
            if user_message.strip() in status_map:
                task_id = session_state.get("selected_task")
                with Session(engine) as session:
                    task = session.get(Task, task_id)
                    if task:
                        task.status = status_map[user_message.strip()]
                        session.add(task)
                        session.commit()
                        session_state["mode"] = "free"
                        session_state["pending_action"] = None
                        return {"response": f"✅ Estado de '{task.title}' actualizado a: {task.status}", "action": "task_updated"}
            return {"response": "Selecciona 1, 2 o 3 para el estado."}
        
        # Si está editando título
        if session_state.get("mode") == "edit_title":
            new_title = user_message.strip()
            if len(new_title) > 0:
                task_id = session_state.get("selected_task")
                with Session(engine) as session:
                    task = session.get(Task, task_id)
                    if task:
                        old_title = task.title
                        task.title = new_title
                        session.add(task)
                        session.commit()
                        session_state["mode"] = "free"
                        session_state["pending_action"] = None
                        return {"response": f"✅ '{old_title}' → '{new_title}'", "action": "title_updated"}
            session_state["mode"] = "free"
            session_state["pending_action"] = None
            return {"response": "Cancelado. Escribe 'ayuda' para el menú."}
    
    # Verificar si es selección de menú
    menu_num = re.match(r'^([1-9])$', user_message.strip())
    if menu_num:
        option = int(menu_num.group(1))
        
        with Session(engine) as session:
            pending_tasks = session.exec(select(Task).where(Task.owner == username, Task.status != "done")).all()
            all_tasks = session.exec(select(Task).where(Task.owner == username)).all()
            
            if option == 1:
                return {"response": "✏️ CREAR TAREA\n\nEscribe el nombre de la tarea:\nEj: 'crear tarea preparar cena' o solo 'preparar cena'"}
            
            elif option == 2:
                if not all_tasks:
                    return {"response": "📭 No tienes tareas. Crea una primero."}
                return {"response": f"✏️ MODIFICAR TAREA\n\nTus tareas:\n" + "\n".join([f"{i+1}. {t.title}" for i, t in enumerate(all_tasks)]) + "\n\nEscribe el número de la tarea:"}
            
            elif option == 3:
                if not pending_tasks:
                    return {"response": "📭 No tienes tareas pendientes."}
                return {"response": f"🔄 MODIFICAR ESTADO\n\nTareas pendientes:\n" + "\n".join([f"{i+1}. {t.title}" for i, t in enumerate(pending_tasks)]) + "\n\nEscribe el número:"}
            
            elif option == 4:
                if not pending_tasks:
                    return {"response": "📭 No tienes tareas para agregar foto."}
                return {"response": f"📷 AGREGAR FOTO\n\nTareas:\n" + "\n".join([f"{i+1}. {t.title}" for i, t in enumerate(pending_tasks)]) + "\n\nEscribe el número:"}
            
            elif option == 5:
                if not all_tasks:
                    return {"response": "📭 No tienes tareas."}
                pending = [t for t in all_tasks if t.status == "todo"]
                progress = [t for t in all_tasks if t.status == "in_progress"]
                done = [t for t in all_tasks if t.status == "done"]
                response = f"📋 TUS TAREAS ({len(all_tasks)})\n⏳{len(pending)} | 🔄{len(progress)} | ✅{len(done)}\n\n"
                if pending:
                    response += "⏳ PENDIENTES:\n" + "\n".join([f"  #{t.id} • {t.title}" for t in pending]) + "\n"
                if progress:
                    response += "\n🔄 EN REVISIÓN:\n" + "\n".join([f"  #{t.id} • {t.title}" for t in progress]) + "\n"
                if done:
                    response += "\n✅ COMPLETADAS:\n" + "\n".join([f"  #{t.id} • {t.title}" for t in done])
                return {"response": response}
            
            elif option == 6:
                session_state["pending_action"] = "complete"
                if not pending_tasks:
                    return {"response": "📭 No tienes tareas pendientes."}
                return {"response": f"✅ COMPLETAR TAREA\n\nTareas:\n" + "\n".join([f"{i+1}. {t.title}" for i, t in enumerate(pending_tasks)]) + "\n\nEscribe el número:"}
            
            elif option == 7:
                session_state["pending_action"] = "delete"
                if not all_tasks:
                    return {"response": "📭 No tienes tareas."}
                return {"response": f"🗑️ ELIMINAR TAREA\n\nTareas:\n" + "\n".join([f"{i+1}. {t.title}" for i, t in enumerate(all_tasks)]) + "\n\nEscribe el número:"}
            
            elif option == 8:
                with Session(engine) as session:
                    tasks = session.exec(select(Task).where(Task.owner == username)).all()
                    if not tasks:
                        return {"response": "📊 No tienes tareas aún."}
                    total = len(tasks)
                    done = len([t for t in tasks if t.status == "done"])
                    pct = (done / total * 100) if total > 0 else 0
                    return {"response": f"📊 ESTADÍSTICAS\n═" * 10 + f"\nTotal: {total}\nCompletadas: {done} ({pct:.0f}%)\nPendientes: {total - done}"}
            
            elif option == 9:
                return {"response": f"👋 ¡Hasta luego, {username}!"}
            
            else:
                return {"response": "Opción no válida."}
    
    # Menú de ayuda
    if any(w in user_message for w in ["ayuda", "help", "comandos", "menu", "opciones"]):
        return {"response": f"""📋 MENÚ DE OPCIONES

1️⃣ Crear tarea
2️⃣ Modificar tarea (cambiar nombre)
3️⃣ Modificar estado de tarea
4️⃣ Agregar foto a una tarea
5️⃣ Mostrar lista de tareas
6️⃣ Completar tarea
7️⃣ Eliminar tarea
8️⃣ Ver estadísticas
9️⃣ Salir

Escribe el número (1-9) o usa un comando como 'crea tarea preparar cena'."""}
    
    # ==================== SALUDOS ====================
    if any(w in user_message for w in ["hola", "hi", "hello", "hey", "buenos", "buenas", "qué tal", "qué onda"]):
        return {"response": f"Hola {username}! 👋\n\nEscribe 'ayuda' para ver el menú de opciones."}
    
    # ==================== MENÚ PRINCIPAL (reemplaza ayuda vieja) ====================
    # Este bloque debe estar ANTES del menú interactivo para que el menú old no se active
    if any(w in user_message for w in ["gracias", "thanks", "thank", "thx", "gracias por"]):
        return {"response": "¡De nada! 😊 Estoy aquí para ayudarte.\n\n¿Algo más en lo que pueda asistirte?"}
    
    # ==================== DESPEDIDAS ====================
    if any(w in user_message for w in ["adiós", "bye", "salir", "hasta luego", "nos vemos", "chao"]):
        return {"response": f"¡Hasta luego, {username}! 👋\n\nQue tengas un día muy productivo. ✨"}
    
    # ==================== QUÉ ES TASKFLOW ====================
    if "?" in user_message or any(w in user_message for w in ["cómo", "qué es", "explica", "qué es taskflow", "what is"]):
        response = """🤖 TASKFLOW - Tu Asistente de Tareas

TaskFlow es una app de gestión de tareas con IA integrada que te permite:

✅ Crear y organizar tareas
✅ Controlar estados (pendiente/en revisión/hecho)
✅ Hablarme naturalmente
✅ Ver estadísticas de progreso
✅ Y mucho más...

Solo dime qué necesitas en lenguaje natural:
• 'crea tarea preparar presentación'
• 'mis tareas'
• 'cómo voy con mi progreso'

¡Pruébalo! 🚀"""
        return {"response": response}
    
    # ==================== RESPUESTA POR DEFECTO CON ANÁLISIS ====================
    # Intentar detectar si el usuario quiere algo sin usar comandos exactos
    msg = user_message.strip()
    cleaned_msg_title = clean_task_title(original_message)
    
    # Si parece ser un nombre de tarea (2-10 palabras cortas)
    words = msg.split()
    if 2 <= len(words) <= 10 and len(msg) <= 100:
        common_words = ["hola", "ayuda", "gracias", "como", "que", "por", "para", "una", "con", "sin", "del", "las", "los", "son", "hay", "tiene", "tengo", "quiero", "necesito", "puedo", "hacer", "pues", "ya", "ahora", "después", "luego", "bien", "mal", "bueno", "buena"]
        content_words = [w for w in words if w.lower() not in common_words]
        if len(content_words) >= 1:
            # Probablemente es una tarea sin decir "crea"
            with Session(engine) as session:
                # Verificar si es una tarea existente
                existing = session.exec(select(Task).where(Task.title.ilike(f"%{cleaned_msg_title}%"), Task.owner == username)).first()
                if cleaned_msg_title and not existing:
                    # Crear como nueva tarea
                    new_task = Task(title=cleaned_msg_title.title() if cleaned_msg_title.islower() else cleaned_msg_title, description="", owner=username)
                    session.add(new_task)
                    session.commit()
                    session.refresh(new_task)
                    session_state["mode"] = "awaiting_description_decision"
                    session_state["pending_action"] = "ask_description"
                    session_state["selected_task"] = new_task.id
                    return {"response": f"✅ Creé la tarea: '{new_task.title}'\n🆔 ID: #{new_task.id}\n\n¿Le pongo descripción?", "action": "task_created", "task_id": new_task.id}
    
    return {"response": f"❓ No entendí. Puedes decirme en lenguaje natural qué necesitas.\n\nEjemplos:\n• 'Crea una tarea llamada comprar leche con descripción del supermercado'\n• 'Crea tarea estudiar para el examen de matemáticas'\n• 'Quiero crear algo: preparar cena de navidad'\n\n¿O prueba 'ayuda' para ver comandos."}


# ==================== CHATBOT V2 MEJORADO ====================

@app.post("/chatbot/v2")
def chatbot_v2(payload: ChatbotPayload, current_user: User = Depends(get_current_user)):
    user_message = payload.message.lower()
    original_message = payload.message
    username = current_user.username
    is_admin = current_user.is_admin
    
    import re
    
    # ==================== COMANDOS SIMPLIFICADOS ====================
    
    # --- CREAR TAREA SIMPLE: "crea [nombre]" o "crear [nombre]" ---
    crea_match = re.search(r'^(?:crea[r]?|nueva[t]?)\s+(.+)', user_message)
    if crea_match:
        task_title = crea_match.group(1).strip()
        with Session(engine) as session:
            new_task = Task(title=task_title, owner=username, status="todo")
            session.add(new_task)
            session.commit()
            return {"response": f"[OK] Tarea creada: {task_title} (ID: #{new_task.id})"}
    
    # --- SALUDOS AND SALUDOS CON AYUDA ---
    if user_message.strip() == "?":
        return {"response": f"Hola {username}! Escribe 'ayuda' para ver comandos."}
    
    # Responder a cualquier cosa que tenga sentido aunque no sea un comando exacto
    # Si el mensaje tiene 3+ palabras y parece tarea, crear
    palabras = user_message.strip().split()
    if len(palabras) >= 2 and len(palabras) <= 15 and not any(w in user_message for w in ["ayuda", "stats", "mis", "tareas", "completa", "elimina", "borra", "busca"]):
        # Probably a task name - assume crear
        task_title = original_message.strip()
        if len(task_title) > 2 and len(task_title) < 100:
            with Session(engine) as session:
                new_task = Task(title=task_title, owner=username, status="todo")
                session.add(new_task)
                session.commit()
                return {"response": f"[OK] Tarea creada: '{task_title}' (ID: #{new_task.id})"}
    
    # --- SALUDOS ---
    saludos = ["hola", "hi", "hello", "hey", "buenas", "buenos", "que tal", "que onda", "wenas", "holis", "buen dia", "buenas tardes", "buenas noches", "buen tarde", "buen mañana"]
    if any(s in user_message for s in saludos):
        return {"response": f"Hola {username}! Soy tu asistente de TaskFlow.\n\nPuedes:\n- Decir 'ayuda' para ver comandos\n- Escribir 'mis tareas' para ver\n- Escribir 'crea [nombre]' para crear\n\nQue necesitas?"}
    
# --- ACCIONES EN LENGUAJE NATURAL ---
    
# "editar" / "modificar" / "cambiar" / "renombrar" -> editar tarea
    if any(f in user_message for f in ["editar", "modificar", "cambiar", "renombrar", "renombra", "cambia eso"]):
        id_match = re.search(r'#?(\d+)', user_message)
        if id_match:
            task_id = int(id_match.group(1))
            new_match = re.search(r'(?:a|por)\s+(.+)$', user_message)
            if new_match:
                new_title = new_match.group(1).strip()
                with Session(engine) as session:
                    task = session.get(Task, task_id)
                    if task and (task.owner == username or is_admin):
                        task.title = new_title
                        session.add(task)
                        session.commit()
                        return {"response": f"[OK] #{task.id} -> '{new_title}'"}
            return {"response": f"[?] Escribe: 'cambia #ID a [nuevo nombre]'"}
    
    # "quiero crear" / "necesito hacer" / "tengo que" / "agrega" / "nueva tarea" -> crear
    crear_frases = ["quiero crear", "necesito hacer", "tengo que hacer", "hice una", "quiero agregar", "voy a crear", "podrias crear", "agrega", "nueva tarea", "nueva", "creame", "hazme", "ponme una", "agregame", "quiero una nueva", "haré una"]
    if any(f in user_message for f in crear_frases):
        # Extraer el nombre de la tarea
        match = re.search(r'(?:crear|agregar|hacer|falta|nueva|hazme|ponme|agregame)\s+(?:una\s+)?(?:tarea\s+)?(?:que\s+)?(.+)', user_message)
        if match:
            task_title = match.group(1).strip()
            if task_title and len(task_title) > 1:
                with Session(engine) as session:
                    new_task = Task(title=task_title, owner=username, status="todo")
                    session.add(new_task)
                    session.commit()
                    return {"response": f"[OK] Tarea creada: '{task_title}' (ID: #{new_task.id})"}
    
    # "ya la hice" / "ya termine" / "listo" / "done" / "completa" -> completar
    completar_frases = ["ya la hice", "ya termine", "ya completada", "ya done", "marcar como faite", "marcar como hecho", "listo con", "terminado", "completa", "done", "hecho", "ya esta", "ya está", "listo"]
    if any(f in user_message for f in completar_frases):
        # Buscar por ID o nombre
        match = re.search(r'(?:la|de|con|el|que)\s+[#]?(\d+)|([a-zA-Z\s]+)', user_message)
        if match:
            task_id = match.group(1)
            task_search = match.group(2) if match.group(2) else ""
            task_search = task_search.strip() if task_search else ""
            with Session(engine) as session:
                task = None
                if task_id:
                    task = session.get(Task, int(task_id))
                elif task_search:
                    task = session.exec(select(Task).where(Task.title.ilike(f"%{task_search}%"), Task.owner == username).first())
                if task and (task.owner == username or is_admin):
                    task.status = "done"
                    session.add(task)
                    session.commit()
                    return {"response": f"[OK] '{task.title}' marcada como faite"}
    
    # "borra" / "elimina" / "quitar" -> eliminar
    eliminar_frases = ["borra", "elimina", "quitar", "borrar", "delete", "quitame", "eliminar", "sacame", "quitale"]
    if any(f in user_message for f in eliminar_frases):
        match = re.search(r'(?:la|de|el)\s+[#]?(\d+)|([a-zA-Z\s]+)', user_message)
        if match:
            task_id = match.group(1)
            task_search = match.group(2).strip() if match.group(2) else ""
            with Session(engine) as session:
                task = None
                if task_id:
                    task = session.get(Task, int(task_id))
                elif task_search:
                    task = session.exec(select(Task).where(Task.title.ilike(f"%{task_search}%"), Task.owner == username).first())
                if task and (task.owner == username or is_admin):
                    task_title = task.title
                    session.delete(task)
                    session.commit()
                    return {"response": f"[OK] '{task_title}' eliminada"}
    
    # "cuantas tareas" / "cuanto tengo" -> stats/contador
    if any(f in user_message for f in ["cuantas tareas", "cuanto tengo", "dime mis tareas", "cuantas tengo", "cuantos pendientes"]):
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.owner == username)).all()
            total = len(tasks)
            done = len([t for t in tasks if t.status == "done"])
            pending = len([t for t in tasks if t.status == "todo"])
            pct = (done / total * 100) if total > 0 else 0
            return {"response": f"[INFO] Tienes {total} tareas. {done} hechas, {pending} pendientes ({pct:.0f}% completadas)"}
    
    # "muestrame" / "ver" / "dame" -> listar tareas
    if any(f in user_message for f in ["muestrame", "dame", "ver mis", "quiero ver", "mostrame mis", "dime mis"]):
        if "tareas" in user_message or "todas" in user_message:
            with Session(engine) as session:
                tasks = session.exec(select(Task).where(Task.owner == username)).all()
                if not tasks:
                    return {"response": "[INFO] No tienes tareas todavia. Escribe 'crea [nombre]' para crear una."}
                response = f"[TUS TAREAS] ({len(tasks)}):\n"
                for t in tasks[:15]:
                    status_icon = "[ ]" if t.status == "todo" else "[~]" if t.status == "in_progress" else "[X]"
                    response += f"{status_icon} #{t.id} - {t.title}\n"
                return {"response": response}
    
    # "buscar" / "encontrar" -> buscar
    if any(f in user_message for f in ["busca", "buscar", "encontra", "busca si hay"]):
        match = re.search(r'(?:busca|buscar|encontra)\s+(?:una\s+)?(?:tarea\s+)?(?:de\s+)?(.+)', user_message)
        if match:
            search_term = match.group(1).strip()
            with Session(engine) as session:
                tasks = session.exec(select(Task).where(Task.title.ilike(f"%{search_term}%"), Task.owner == username)).all()
                if not tasks:
                    return {"response": f"[INFO] No encontre tareas con: {search_term}"}
                response = f"[RESULTADOS] ({len(tasks)}:\n"
                for t in tasks[:10]:
                    response += f"#{t.id} - {t.title}\n"
                return {"response": response}
    
    # "limpiar" / "borrar completadas" -> limpiar
    if any(f in user_message for f in ["limpiar", "limpia", "borrar completadas", "borra las feitas"]):
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.owner == username, Task.status == "done")).all()
            if not tasks:
                return {"response": "[OK] No hay tareas completadas para limpiar."}
            count = len(tasks)
            for t in tasks:
                session.delete(t)
            session.commit()
            return {"response": f"[OK] {count} tareas completadas eliminadas", "action": "cleanup_done"}
    
    # "agregar foto" / "subir imagen" -> foto
    if any(f in user_message for f in ["agregar foto", "subir foto", "imagen", "foto de la"]):
        match = re.search(r'(?:foto|imagen)\s+(?:de\s+)?([#]?\d+|[a-z\s]+)', user_message)
        if match:
            task_search = match.group(1).strip().replace("#", "")
            task_id_match = re.search(r'(\d+)', task_search)
            with Session(engine) as session:
                if task_id_match:
                    task = session.get(Task, int(task_id_match.group(1)))
                else:
                    task = session.exec(select(Task).where(Task.title.ilike(f"%{task_search}%"), Task.owner == username)).first()
                if task:
                    return {"response": f"[FOTO] Para agregar foto a '{task.title}': POST /tasks/{task.id}/image con archivo jpg/png", "action": "photo_upload", "task_id": task.id}
    
    # ==================== COMANDOS SIMPLIFICADOS ====================
    
    # --- CREAR TAREA SIMPLE: "crea [nombre]" o "crear [nombre]" ---
    crea_match = re.search(r'^(?:crea[r]?|nueva[t]?)\s+(.+)', user_message)
    if crea_match:
        task_title = crea_match.group(1).strip()
        with Session(engine) as session:
            new_task = Task(title=task_title, owner=username, status="todo")
            session.add(new_task)
            session.commit()
            return {"response": f"[OK] Tarea creada: {task_title} (ID: #{new_task.id})", "action": "task_created", "task_id": new_task.id}
    
    # --- COMPLETAR: "completa [nombre o #ID]" o "done [nombre]" ---
    completa_match = re.search(r'^(?:completa|done|hecho|listo)\s+(?:tarea\s+)?#?(.+)', user_message)
    if completa_match:
        task_search = completa_match.group(1).strip()
        task_id_match = re.search(r'(\d+)', task_search)
        with Session(engine) as session:
            if task_id_match:
                task = session.get(Task, int(task_id_match.group(1)))
            else:
                task = session.exec(select(Task).where(Task.title.ilike(f"%{task_search}%"), Task.owner == username).first())
            if task and (task.owner == username or is_admin):
                task.status = "done"
                session.add(task)
                session.commit()
                return {"response": f"[OK] '{task.title}' marcada como hecha", "action": "task_completed"}
            return {"response": f"No encontrada: {task_search}"}
    
    # --- ELIMINAR: "elimina [nombre o #ID]" or "borra [nombre]" ---
    elimina_match = re.search(r'^(?:elimina|borra|delete)\s+(?:tarea\s+)?#?(.+)', user_message)
    if elimina_match:
        task_search = elimina_match.group(1).strip()
        task_id_match = re.search(r'(\d+)', task_search)
        with Session(engine) as session:
            if task_id_match:
                task = session.get(Task, int(task_id_match.group(1)))
            else:
                task = session.exec(select(Task).where(Task.title.ilike(f"%{task_search}%"), Task.owner == username).first())
            if task and (task.owner == username or is_admin):
                task_title = task.title
                session.delete(task)
                session.commit()
                return {"response": f"[OK] '{task_title}' eliminada", "action": "task_deleted"}
            return {"response": f"No encontrada: {task_search}"}
    
    # --- BUSCAR: "busca [palabra]" ---
    busca_match = re.search(r'^busca\s+(.+)', user_message)
    if busca_match:
        search_term = busca_match.group(1).strip()
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.title.ilike(f"%{search_term}%"), Task.owner == username).all())
            if not tasks:
                return {"response": f"No hay tareas con: {search_term}"}
            response = f"[RESULTADOS] ({len(tasks)}):\n"
            for t in tasks[:10]:
                response += f"#{t.id} - {t.title} [{t.status}]\n"
            return {"response": response}
    
    # --- PENDIENTES: "pendientes" or "pendientes mias" ---
    if any(w in user_message for w in ["pendientes", "tareas pendientes", "por hacer"]):
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.owner == username, Task.status == "todo")).all()
            if not tasks:
                return {"response": "[OK] No tienes tareas pendientes."}
            response = f"[PENDIENTES] ({len(tasks)}):\n"
            for t in tasks[:15]:
                response += f"#{t.id} - {t.title}\n"
            return {"response": response}
    
    # --- COMPLETADAS: "completadas" or "hechas" ---
    if any(w in user_message for w in ["completadas", "hechas", "done tasks"]):
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.owner == username, Task.status == "done")).all()
            if not tasks:
                return {"response": "[OK] No hay tareas completadas."}
            response = f"[COMPLETADAS] ({len(tasks)}):\n"
            for t in tasks[:15]:
                response += f"#{t.id} - {t.title}\n"
            return {"response": response}
    
    # --- STATS: "stats" or "estadisticas" ---
    if any(w in user_message for w in ["stats", "estadisticas", "informe"]):
        with Session(engine) as session:
            all_tasks = session.exec(select(Task).where(Task.owner == username)).all()
            total = len(all_tasks)
            done = len([t for t in all_tasks if t.status == "done"])
            pending = len([t for t in all_tasks if t.status == "todo"])
            pct = (done / total * 100) if total > 0 else 0
            return {"response": f"[ESTADISTICAS]\nTotal: {total}\nCompletadas: {done} ({pct:.0f}%)\nPendientes: {pending}"}
    
    # --- LIMPIAR: "limpiar" or "limpia completadas" ---
    if any(w in user_message for w in ["limpiar", "limpia", "borrar completadas"]):
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.owner == username, Task.status == "done")).all()
            if not tasks:
                return {"response": "[OK] No hay tareas completadas para limpiar."}
            count = len(tasks)
            for t in tasks:
                session.delete(t)
            session.commit()
            return {"response": f"[OK] {count} tareas completadas eliminadas", "action": "cleanup_done"}
    
    # --- FOTO: "foto [nombre]" (responder con instruccion para subir) ---
    foto_match = re.search(r'^(?:foto|imagen|subir foto)\s+(?:tarea\s+)?#?(.+)', user_message)
    if foto_match:
        task_search = foto_match.group(1).strip()
        task_id_match = re.search(r'(\d+)', task_search)
        with Session(engine) as session:
            if task_id_match:
                task = session.get(Task, int(task_id_match.group(1)))
            else:
                task = session.exec(select(Task).where(Task.title.ilike(f"%{task_search}%"), Task.owner == username)).first()
            if task:
                return {"response": f"[FOTO] Para agregar foto a '{task.title}': POST /tasks/{task.id}/image con archivo jpg/png", "action": "photo_upload", "task_id": task.id}
            return {"response": f"No encontrada: {task_search}"}
    
    # ==================== PRIORIDAD DE TAREA ====================
    prioridad_match = re.search(r'prioridad[:\s]*(alta|media|baja|urgente)', original_message, re.IGNORECASE)
    if prioridad_match:
        prioridad = prioridad_match.group(1).lower()
        
        task_id_match = re.search(r'#?(\d+)', user_message)
        if task_id_match:
            task_id = int(task_id_match.group(1))
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if task and (task.owner == username or is_admin):
                    task.priority = prioridad
                    session.add(task)
                    session.commit()
                    return {"response": f"⭐ Prioridad de '{task.title}' cambiada a: {prioridad.upper()}", "action": "priority_changed"}
        
        title_match = re.search(r'(?:prioridad)[:\s]+"?(.+?)"?\s*(?:a| como)?$', original_message, re.IGNORECASE)
        if title_match:
            title_search = title_match.group(1).strip()
            with Session(engine) as session:
                task = session.exec(select(Task).where(Task.title.ilike(f"%{title_search}%"), Task.owner == username)).first()
                if task:
                    task.priority = prioridad
                    session.add(task)
                    session.commit()
                    return {"response": f"⭐ Prioridad de '{task.title}' cambiada a: {prioridad.upper()}", "action": "priority_changed"}
    
    # ==================== VER TAREAS POR ESTADO ====================
    if any(w in user_message for w in ["pendientes", "tareas pendientes", "por hacer"]):
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.owner == username, Task.status == "todo")).all()
            if not tasks:
                return {"response": "✅ No tienes tareas pendientes."}
            
            response = "⏳ TAREAS PENDIENTES:\n"
            for t in tasks:
                response += f"#{t.id} • {t.title}\n"
            return {"response": response}
    
    if any(w in user_message for w in ["en revision", "en revisión", "revisando"]):
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.owner == username, Task.status == "in_progress")).all()
            if not tasks:
                return {"response": "No tienes tareas en revisión."}
            
            response = "🔄 TAREAS EN REVISIÓN:\n"
            for t in tasks:
                response += f"#{t.id} • {t.title}\n"
            return {"response": response}
    
    if any(w in user_message for w in ["completadas", "hechas", "done tasks", "tareas feitas"]):
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.owner == username, Task.status == "done")).all()
            if not tasks:
                return {"response": "No tienes tareas completadas aún."}
            
            response = f"✅ TAREAS COMPLETADAS ({len(tasks)}):\n"
            for t in tasks[:15]:
                response += f"✓ {t.title}\n"
            if len(tasks) > 15:
                response += f"...y {len(tasks)-15} más"
            return {"response": response}
    
    # ==================== ESTADÍSTICAS DETALLADAS ====================
    if any(w in user_message for w in ["estadisticas", "stats", "progreso", "informe"]):
        with Session(engine) as session:
            all_tasks = session.exec(select(Task).where(Task.owner == username)).all()
            total = len(all_tasks)
            
            pending = len([t for t in all_tasks if t.status == "todo"])
            in_progress = len([t for t in all_tasks if t.status == "in_progress"])
            done = len([t for t in all_tasks if t.status == "done"])
            
            alta = len([t for t in all_tasks if getattr(t, 'priority', None) == 'alta'])
            media = len([t for t in all_tasks if getattr(t, 'priority', None) == 'media'])
            baja = len([t for t in all_tasks if getattr(t, 'priority', None) == 'baja'])
            
            pct = (done / total * 100) if total > 0 else 0
            
            response = f"""📊 ESTADÍSTICAS DE {username}
{'='*25}

📈 GENERAL:
• Total: {total} tareas
• Completadas: {done} ({pct:.0f}%)
• En revisión: {in_progress}
• Pendientes: {pending}

⭐ POR PRIORIDAD:
• Alta: {alta}
• Media: {media}
• Baja: {baja}

{'🎉 Excelente!' if pct >= 80 else '💪 Vas bien!' if pct >= 50 else '🚀 A trabajar!'}"""
            return {"response": response}
    
    # ==================== EDITAR TÍTULO ====================
    if any(w in user_message for w in ["renombra", "renombrar", "cambia nombre", "cambia titulo"]):
        update_match = re.search(r'#(\d+)[:\s]+(.+)', original_message, re.IGNORECASE)
        if update_match:
            task_id = int(update_match.group(1))
            new_title = update_match.group(2).strip()
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if not task:
                    return {"response": f"❌ No encontré tarea #{task_id}"}
                if task.owner != username and not is_admin:
                    return {"response": "❌ Sin permiso"}
                
                old_title = task.title
                task.title = new_title
                session.add(task)
                session.commit()
                return {"response": f"✅ '{old_title}' → '{new_title}'", "action": "title_updated"}
    
    # ==================== DUPLICAR TAREA ====================
    if any(w in user_message for w in ["duplica", "clonar", "copiar"]):
        task_id_match = re.search(r'#?(\d+)', user_message)
        if task_id_match:
            task_id = int(task_id_match.group(1))
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if not task:
                    return {"response": f"❌ No encontré tarea #{task_id}"}
                
                new_task = Task(
                    title=f"{task.title} (copia)",
                    description=task.description,
                    owner=username,
                    status="todo"
                )
                session.add(new_task)
                session.commit()
                session.refresh(new_task)
                return {"response": f"✅ Tarea copiada: '#{new_task.id} {new_task.title}'", "action": "task_duplicated"}
    
    # ==================== TAREA MÁS ANTIGUA ====================
    if any(w in user_message for w in ["primera tarea", "tarea mas antigua", "oldest task"]):
        with Session(engine) as session:
            task = session.exec(select(Task).where(Task.owner == username).order_by(Task.id)).first()
            if not task:
                return {"response": "No tienes tareas."}
            
            status_icon = {"todo": "⏳", "in_progress": "🔄", "done": "✅"}.get(task.status, "⏳")
            return {"response": f"{status_icon} Tu primera tarea (#{task.id}):\n{task.title}\n\n📝 {task.description or 'Sin descripción'}"}
    
    # ==================== TAREA MÁS RECIENTE ====================
    if any(w in user_message for w in ["ultima tarea", "tarea reciente", " newest task", "tarea nueva"]):
        with Session(engine) as session:
            task = session.exec(select(Task).where(Task.owner == username).order_by(Task.id.desc())).first()
            if not task:
                return {"response": "No tienes tareas."}
            
            status_icon = {"todo": "⏳", "in_progress": "🔄", "done": "✅"}.get(task.status, "⏳")
            return {"response": f"{status_icon} Tu tarea más reciente (#{task.id}):\n{task.title}\n\n📝 {task.description or 'Sin descripción'}"}
    
    # ==================== CONTAR TAREAS ====================
    if any(w in user_message for w in ["cuantas", "cuántas", "count", "cuenta"]):
        with Session(engine) as session:
            total = len(session.exec(select(Task).where(Task.owner == username)).all())
            pending = len(session.exec(select(Task).where(Task.owner == username, Task.status == "todo")).all())
            done = len(session.exec(select(Task).where(Task.owner == username, Task.status == "done")).all())
            
            return {"response": f"📊 Tienes:\n• {total} total\n• {pending} pendientes\n• {done} completadas"}
    
    # ==================== LIMPIAR TAREAS COMPLETADAS ====================
    if any(w in user_message for w in ["limpiar", "borrar completadas", "clear done"]):
        with Session(engine) as session:
            tasks = session.exec(select(Task).where(Task.owner == username, Task.status == "done")).all()
            if not tasks:
                return {"response": "No hay tareas completadas para limpiar."}
            
            count = len(tasks)
            for t in tasks:
                session.delete(t)
            session.commit()
            return {"response": f"🧹 {count} tareas completadas eliminadas.", "action": "cleanup_done"}
    
    # ==================== FECHA DE CREACIÓN ====================
    if any(w in user_message for w in ["cuando cree", "fecha creacion", "cuando"]):
        task_id_match = re.search(r'#?(\d+)', user_message)
        if task_id_match:
            task_id = int(task_id_match.group(1))
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if task:
                    created = getattr(task, 'created_at', None)
                    if created:
                        return {"response": f"📅 '{task.title}' fue creada el {created.strftime('%d/%m/%Y %H:%M')}"}
                    return {"response": f"📅 '{task.title}' - ID: #{task.id}"}
    
# ==================== AYUDA V2 ====================
    if any(w in user_message for w in ["ayuda", "help", "comandos", "?"]):
        ayuda_msg = """COMANDOS:

[CREAR]
- crea [nombre]

[VER]
- mis tareas
- pendientes
- completadas

[EDITAR]
- completa [nombre o #ID]
- elimina [nombre o #ID]
- foto [nombre]

[BUSCAR]
- busca [palabra]

[ESTADISTICAS]
- stats

[MANTENIMIENTO]
- limpiar

Escribe lo que necesitas."""
        return {"response": ayuda_msg}

    # ==================== FALLBACK INTELIGENTE ====================
    # Si no entiende el comando, intenta inferir la accion
    msg = user_message
    
    # Detectar si es una tarea por ID
    task_id_match = re.search(r'[#]?(\d+)', msg)
    
    with Session(engine) as session:
        task = None
        if task_id_match:
            task = session.get(Task, int(task_id_match.group(1)))
        else:
            # Buscar por titulo parcial
            potential_title = msg.strip()
            if len(potential_title) > 2:
                task = session.exec(select(Task).where(Task.title.ilike(f"%{potential_title}%"), Task.owner == username)).first()
        
        if task:
            # Hay una tarea, determinar accion
            if any(w in msg for w in ["hecho", "completa", "done", "listo", "terminado", "x"]):
                task.status = "done"
                session.add(task)
                session.commit()
                return {"response": f"[OK] '{task.title}' marcada como faite", "action": "task_completed"}
            elif any(w in msg for w in ["borra", "elimina", "quit", "delete"]):
                task_title = task.title
                session.delete(task)
                session.commit()
                return {"response": f"[OK] '{task_title}' eliminada", "action": "task_deleted"}
            elif any(w in msg for w in ["foto", "imagen"]):
                return {"response": f"[FOTO] Para agregar foto a '{task.title}': POST /tasks/{task.id}/image", "action": "photo_upload", "task_id": task.id}
            elif any(w in msg for w in ["ver", "detalle", "info", "muestrame"]):
                return {"response": f"[INFO] #{task.id} - {task.title}\nEstado: {task.status}\nDescripcion: {task.description or 'Sin descripcion'}"}
            else:
                return {"response": f"[?] Para '{task.title}': escribe 'completa' o 'elimina' o 'foto' o 'ver'"}

    # Si hay palabras clave pero no hay tarea
    if any(w in msg for w in ["tareas", "tarea", "tengo", "mis"]):
        with Session(engine) as session:
            if any(w in msg for w in ["cuantas", "cuanto", "dime", "cuantos"]):
                tasks = session.exec(select(Task).where(Task.owner == username)).all()
                total = len(tasks)
                done = len([t for t in tasks if t.status == "done"])
                pending = len([t for t in tasks if t.status == "todo"])
                return {"response": f"[INFO] Tienes {total} tareas. {done} feitas, {pending} pendientes."}
            else:
                tasks = session.exec(select(Task).where(Task.owner == username)).all()
                if not tasks:
                    return {"response": "[INFO] No tienes tareas. Escribe 'crea [nombre]' para crear una."}
                response = f"[TUS TAREAS] ({len(tasks)}):\n"
                for t in tasks[:10]:
                    response += f"#{t.id} - {t.title}\n"
                return {"response": response}
    
    if any(w in msg for w in ["crea", "nueva", "agregar", "hacer"]):
        match = re.search(r'(?:crea|nueva|agregar|hacer)\s+(?:una\s+)?(?:tarea\s+)?(.+)', msg)
        if match and match.group(1).strip():
            task_title = match.group(1).strip()
            with Session(engine) as session:
                new_task = Task(title=task_title, owner=username, status="todo")
                session.add(new_task)
                session.commit()
                return {"response": f"[OK] Tarea creada: {task_title} (ID: #{new_task.id})", "action": "task_created"}

    return {"response": "No entendi. Prueba 'ayuda' para ver todos los comandos."}
