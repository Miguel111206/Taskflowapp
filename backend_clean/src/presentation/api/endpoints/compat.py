import base64
import io
import re
from datetime import datetime, timedelta
from typing import Optional

import pyotp
import qrcode
from qrcode.image.svg import SvgImage
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.infrastructure.auth.jwt_handler import JWTHandler
from src.infrastructure.auth.password_handler import PasswordHandler
from src.infrastructure.database.session import get_session
from src.infrastructure.models.task_model import TaskModel
from src.infrastructure.models.user_model import UserModel

router = APIRouter(tags=["Frontend compatibility"])
security = HTTPBearer(auto_error=False)

TODO_TO_CLEAN = {
    "todo": "pending",
    "in_progress": "in_progress",
    "done": "completed",
    "cancelled": "cancelled",
}

CLEAN_TO_FRONTEND = {
    "pending": "todo",
    "in_progress": "in_progress",
    "completed": "done",
    "cancelled": "cancelled",
}

MAX_LOGIN_ATTEMPTS = 5
LOCK_MINUTES = 15


class RegisterPayload(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class TaskPayload(BaseModel):
    title: str
    description: str = ""
    owner: Optional[str] = None


class Verify2FAPayload(BaseModel):
    username: str = ""
    code: str


class ChatbotPayload(BaseModel):
    message: str


def get_db():
    yield from get_session()


def _token_payload(user: UserModel) -> dict:
    return {"sub": user.username, "user_id": user.id, "role": user.role}


def _token_response(user: UserModel) -> dict:
    handler = JWTHandler()
    payload = _token_payload(user)
    return {
        "access_token": handler.create_access_token(payload),
        "refresh_token": handler.create_refresh_token(payload),
        "token_type": "bearer",
    }


def _current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> UserModel:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        payload = JWTHandler().verify_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(UserModel).filter(UserModel.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _require_admin(current_user: UserModel = Depends(_current_user)) -> UserModel:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _user_response(user: UserModel) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "is_admin": user.role == "admin",
        "role": user.role,
        "is_2fa_enabled": bool(user.is_2fa_enabled),
    }


def _task_response(task: TaskModel, owner: Optional[UserModel] = None) -> dict:
    owner_username = owner.username if owner else task.owner_id
    has_image = bool(getattr(task, "image", None))
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description or "",
        "status": CLEAN_TO_FRONTEND.get(task.status, task.status),
        "owner": owner_username,
        "image": task.image if has_image else None,
        "priority": "media",
        "created_at": task.created_at,
    }


def _task_with_owner(db: Session, task: TaskModel) -> dict:
    owner = db.query(UserModel).filter(UserModel.id == task.owner_id).first()
    return _task_response(task, owner)


def _email_for(payload: RegisterPayload) -> str:
    if payload.email:
        return payload.email
    safe_username = "".join(ch for ch in payload.username.lower() if ch.isalnum() or ch in "._-")
    return f"{safe_username or 'user'}@taskflow.local"


def _check_login_allowed(user: UserModel) -> None:
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(status_code=423, detail="Account temporarily locked")


def _record_failed_login(user: UserModel, db: Session) -> None:
    user.login_attempts = (user.login_attempts or 0) + 1
    if user.login_attempts >= MAX_LOGIN_ATTEMPTS:
        user.locked_until = datetime.utcnow() + timedelta(minutes=LOCK_MINUTES)
    db.commit()


def _record_successful_login(user: UserModel, db: Session) -> None:
    user.login_attempts = 0
    user.locked_until = None
    db.commit()


def _find_task_for_user(db: Session, user: UserModel, query: str = "") -> Optional[TaskModel]:
    query = query.strip()
    id_match = re.search(r"#?([0-9a-fA-F-]{8,})", query)
    if id_match:
        task = db.query(TaskModel).filter(TaskModel.id.startswith(id_match.group(1))).first()
        if task and (user.role == "admin" or task.owner_id == user.id):
            return task

    cleanup = re.sub(
        r"\b(foto|imagen|subir|agregar|ponle|a|de|la|el|tarea|completa|completar|elimina|borra|ver|detalle|estado)\b",
        " ",
        query,
        flags=re.IGNORECASE,
    ).strip()
    task_query = db.query(TaskModel)
    if user.role != "admin":
        task_query = task_query.filter(TaskModel.owner_id == user.id)
    if cleanup:
        found = task_query.filter(TaskModel.title.ilike(f"%{cleanup}%")).first()
        if found:
            return found
    return task_query.first()


def _format_tasks(tasks: list[TaskModel]) -> str:
    if not tasks:
        return "No tienes tareas."
    lines = []
    for task in tasks[:15]:
        status = CLEAN_TO_FRONTEND.get(task.status, task.status)
        lines.append(f"#{task.id[:8]} - {task.title} [{status}]")
    if len(tasks) > 15:
        lines.append(f"...y {len(tasks) - 15} mas")
    return "\n".join(lines)


@router.post("/register")
def register(payload: RegisterPayload, db: Session = Depends(get_db)):
    if db.query(UserModel).filter(UserModel.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = UserModel(
        username=payload.username,
        email=_email_for(payload),
        password_hash=PasswordHandler().hash(payload.password),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, **_token_response(user)}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    _check_login_allowed(user)
    if not PasswordHandler().verify(form_data.password, user.password_hash):
        _record_failed_login(user, db)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_2fa_enabled:
        db.commit()
        return {"access_token": "", "refresh_token": "", "token_type": "bearer"}
    _record_successful_login(user, db)
    return _token_response(user)


@router.post("/login_json")
def login_json(payload: RegisterPayload, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    _check_login_allowed(user)
    if not PasswordHandler().verify(payload.password, user.password_hash):
        _record_failed_login(user, db)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_2fa_enabled:
        db.commit()
        return {"access_token": "", "refresh_token": "", "token_type": "bearer"}
    _record_successful_login(user, db)
    return _token_response(user)


@router.post("/login/2fa")
def login_2fa(payload: Verify2FAPayload, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == payload.username).first()
    if not user or not user.totp_secret:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    _check_login_allowed(user)
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(str(payload.code).strip(), valid_window=1):
        _record_failed_login(user, db)
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    _record_successful_login(user, db)
    return _token_response(user)


@router.post("/refresh")
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    try:
        payload = JWTHandler().verify_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.query(UserModel).filter(UserModel.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return _token_response(user)


@router.post("/logout")
def logout(current_user: UserModel = Depends(_current_user)):
    return {"message": "Logged out successfully"}


@router.get("/me")
def get_me(current_user: UserModel = Depends(_current_user)):
    return _user_response(current_user)


@router.post("/2fa/setup")
def setup_2fa(current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    if user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA already enabled")
    secret = pyotp.random_base32()
    user.totp_secret = secret
    db.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.username, issuer_name="TaskFlow")

    qr = qrcode.QRCode(version=1, box_size=10, border=5, image_factory=SvgImage)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image()
    buffer = io.BytesIO()
    img.save(buffer)
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    return {"secret": secret, "qr_code": f"data:image/svg+xml;base64,{qr_base64}"}


@router.post("/2fa/enable")
def enable_2fa(payload: Verify2FAPayload, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    if user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA already enabled")
    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA not configured")
    if not pyotp.TOTP(user.totp_secret).verify(str(payload.code).strip(), valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code")
    user.is_2fa_enabled = True
    db.commit()
    return {"message": "2FA enabled successfully"}


@router.post("/2fa/disable")
def disable_2fa(payload: Verify2FAPayload, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    if not user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA not enabled")
    if not user.totp_secret or not pyotp.TOTP(user.totp_secret).verify(str(payload.code).strip(), valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code")
    user.is_2fa_enabled = False
    user.totp_secret = None
    db.commit()
    return {"message": "2FA disabled successfully"}


@router.get("/users")
def list_users(current_user: UserModel = Depends(_require_admin), db: Session = Depends(get_db)):
    return [_user_response(user) for user in db.query(UserModel).all()]


@router.delete("/users/{user_id}")
def delete_user(user_id: str, current_user: UserModel = Depends(_require_admin), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Admins cannot delete their own account")
    db.query(TaskModel).filter(TaskModel.owner_id == user.id).delete()
    db.delete(user)
    db.commit()
    return {"ok": True, "message": f"User {user.username} deleted"}


@router.post("/admin/promote/{username}")
def promote_user(username: str, current_user: UserModel = Depends(_require_admin), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = "admin"
    db.commit()
    return {"message": f"User {username} promoted to admin"}


@router.post("/admin/demote/{username}")
def demote_user(username: str, current_user: UserModel = Depends(_require_admin), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot demote yourself")
    user.role = "user"
    db.commit()
    return {"message": f"User {username} demoted to user"}


@router.post("/tasks")
def create_task(payload: TaskPayload, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    owner = current_user
    if payload.owner and payload.owner != current_user.username:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Cannot create task for another user")
        owner = db.query(UserModel).filter(UserModel.username == payload.owner).first()
        if not owner:
            raise HTTPException(status_code=400, detail="Owner user does not exist")
    task = TaskModel(
        title=payload.title,
        description=payload.description,
        status="pending",
        owner_id=owner.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_response(task, owner)


@router.get("/tasks")
def list_tasks(current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    query = db.query(TaskModel)
    if current_user.role != "admin":
        query = query.filter(TaskModel.owner_id == current_user.id)
    return [_task_with_owner(db, task) for task in query.all()]


@router.get("/tasks/by_user/{username}")
def list_tasks_by_user(username: str, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        return []
    if current_user.role != "admin" and current_user.id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return [_task_response(task, user) for task in db.query(TaskModel).filter(TaskModel.owner_id == user.id).all()]


@router.get("/tasks/by_status/{status}")
def list_tasks_by_status(status: str, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    clean_status = TODO_TO_CLEAN.get(status, status)
    query = db.query(TaskModel).filter(TaskModel.status == clean_status)
    if current_user.role != "admin":
        query = query.filter(TaskModel.owner_id == current_user.id)
    return [_task_with_owner(db, task) for task in query.all()]


@router.get("/tasks/{task_id}")
def get_task(task_id: str, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role != "admin" and task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return _task_with_owner(db, task)


@router.put("/tasks/{task_id}")
def update_task(task_id: str, payload: TaskPayload, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role != "admin" and task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    task.title = payload.title
    task.description = payload.description
    db.commit()
    db.refresh(task)
    return _task_with_owner(db, task)


@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role != "admin" and task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(task)
    db.commit()
    return {"ok": True}


@router.patch("/tasks/{task_id}/status")
def change_task_status(task_id: str, status: str, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role != "admin" and task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    task.status = TODO_TO_CLEAN.get(status, status)
    db.commit()
    db.refresh(task)
    return _task_with_owner(db, task)


@router.post("/tasks/{task_id}/image")
async def upload_task_image(task_id: str, file: UploadFile, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Unsupported image type")
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role != "admin" and task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    image_data = base64.b64encode(contents).decode("utf-8")
    task.image = f"data:{file.content_type or 'image/png'};base64,{image_data}"
    db.commit()
    return {"image": task.image}


@router.post("/chatbot")
def chatbot_complete(payload: ChatbotPayload, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    original = payload.message.strip()
    message = original.lower()
    task_query = db.query(TaskModel)
    if current_user.role != "admin":
        task_query = task_query.filter(TaskModel.owner_id == current_user.id)

    if any(word in message for word in ["ayuda", "help", "comandos", "?"]):
        return {"response": "COMANDOS:\n- crea [nombre]\n- mis tareas / pendientes / completadas\n- completa [nombre o #id]\n- elimina [nombre o #id]\n- estado #id pendiente|revision|completado\n- busca [palabra]\n- foto [nombre o #id]\n- stats"}

    create_match = re.search(r"^(?:crea|crear|nueva|nuevo|agrega|agregar|hacer)\s+(?:una\s+)?(?:tarea\s+)?(.+)", original, re.IGNORECASE)
    if create_match:
        title = create_match.group(1).strip()
        if not title:
            return {"response": "Dime el nombre de la tarea."}
        task = TaskModel(title=title, description="", status="pending", owner_id=current_user.id)
        db.add(task)
        db.commit()
        db.refresh(task)
        return {"response": f"Tarea creada: #{task.id[:8]} - {task.title}", "action": "task_created", "task_id": task.id}

    if any(word in message for word in ["foto", "imagen", "subir foto", "agregar foto", "ponle foto"]):
        task = _find_task_for_user(db, current_user, original)
        if not task:
            return {"response": "No encontre la tarea para agregar foto. Dame el nombre o ID."}
        return {
            "response": f"Para agregar foto a '{task.title}': usa el boton Subir foto o POST /tasks/{task.id}/image. Formatos: JPEG, PNG, GIF, WEBP, BMP, SVG, HEIC, HEIF, TIFF y AVIF.",
            "action": "photo_upload",
            "task_id": task.id,
        }

    if any(word in message for word in ["completa", "completar", "termina", "terminar", "hecho", "listo"]):
        task = _find_task_for_user(db, current_user, original)
        if not task:
            return {"response": "No encontre esa tarea para completarla."}
        task.status = "completed"
        db.commit()
        return {"response": f"'{task.title}' marcada como completada.", "action": "task_completed", "task_id": task.id}

    if any(word in message for word in ["elimina", "eliminar", "borra", "borrar", "delete"]):
        task = _find_task_for_user(db, current_user, original)
        if not task:
            return {"response": "No encontre esa tarea para eliminarla."}
        title = task.title
        db.delete(task)
        db.commit()
        return {"response": f"'{title}' eliminada.", "action": "task_deleted"}

    status_match = re.search(r"(?:estado|cambia|cambiar).*?(pendiente|revision|revisi[oó]n|progreso|completado|completa|done|todo|in_progress)", message)
    if status_match:
        task = _find_task_for_user(db, current_user, original)
        if not task:
            return {"response": "No encontre esa tarea para cambiar el estado."}
        raw_status = status_match.group(1)
        status_map = {
            "pendiente": "pending",
            "todo": "pending",
            "revision": "in_progress",
            "revisión": "in_progress",
            "progreso": "in_progress",
            "in_progress": "in_progress",
            "completado": "completed",
            "completa": "completed",
            "done": "completed",
        }
        task.status = status_map.get(raw_status, "pending")
        db.commit()
        return {"response": f"Estado de '{task.title}' actualizado a {CLEAN_TO_FRONTEND.get(task.status, task.status)}.", "action": "status_changed", "task_id": task.id}

    search_match = re.search(r"^(?:busca|buscar|search)\s+(.+)", original, re.IGNORECASE)
    if search_match:
        term = search_match.group(1).strip()
        tasks = task_query.filter(TaskModel.title.ilike(f"%{term}%")).all()
        return {"response": f"RESULTADOS ({len(tasks)}):\n{_format_tasks(tasks)}"}

    if any(word in message for word in ["stats", "estadisticas", "estadísticas", "progreso", "informe"]):
        tasks = task_query.all()
        total = len(tasks)
        done = len([task for task in tasks if task.status == "completed"])
        progress = len([task for task in tasks if task.status == "in_progress"])
        pending = len([task for task in tasks if task.status == "pending"])
        pct = int((done / total) * 100) if total else 0
        return {"response": f"ESTADISTICAS\nTotal: {total}\nCompletadas: {done} ({pct}%)\nEn revision: {progress}\nPendientes: {pending}"}

    if any(word in message for word in ["pendientes", "por hacer"]):
        tasks = task_query.filter(TaskModel.status == "pending").all()
        return {"response": f"PENDIENTES ({len(tasks)}):\n{_format_tasks(tasks)}"}

    if any(word in message for word in ["completadas", "hechas", "done"]):
        tasks = task_query.filter(TaskModel.status == "completed").all()
        return {"response": f"COMPLETADAS ({len(tasks)}):\n{_format_tasks(tasks)}"}

    if any(word in message for word in ["revision", "revisión", "progreso"]):
        tasks = task_query.filter(TaskModel.status == "in_progress").all()
        return {"response": f"EN REVISION ({len(tasks)}):\n{_format_tasks(tasks)}"}

    if any(word in message for word in ["mis tareas", "tareas", "lista", "ver"]):
        tasks = task_query.all()
        return {"response": f"TUS TAREAS ({len(tasks)}):\n{_format_tasks(tasks)}"}

    task = _find_task_for_user(db, current_user, original)
    if task:
        status = CLEAN_TO_FRONTEND.get(task.status, task.status)
        return {"response": f"#{task.id[:8]} - {task.title}\nEstado: {status}\nDescripcion: {task.description or 'Sin descripcion'}"}

    return {"response": "No entendi. Prueba 'ayuda' para ver todos los comandos."}


@router.get("/tasks/{task_id}/image")
def get_task_image(task_id: str, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role != "admin" and task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if not task.image:
        raise HTTPException(status_code=404, detail="Image not found")
    try:
        header, b64 = task.image.split(",", 1)
        media_type = header.split(";")[0].split(":", 1)[1]
        return Response(content=base64.b64decode(b64, validate=True), media_type=media_type)
    except Exception:
        raise HTTPException(status_code=422, detail="Stored image data is invalid")


@router.post("/chatbot")
def chatbot(payload: ChatbotPayload, current_user: UserModel = Depends(_current_user), db: Session = Depends(get_db)):
    message = payload.message.lower().strip()
    if "foto" in message or "imagen" in message:
        task = db.query(TaskModel).filter(TaskModel.owner_id == current_user.id).first()
        if not task:
            return {"response": "No tienes tareas para agregar foto."}
        return {
            "response": f"Para agregar foto a '{task.title}', usa el botón Subir foto.",
            "action": "photo_upload",
            "task_id": task.id,
        }
    if "tarea" in message or "pendiente" in message:
        tasks = db.query(TaskModel).filter(TaskModel.owner_id == current_user.id).all()
        if not tasks:
            return {"response": "No tienes tareas todavía."}
        response = "Tus tareas:\n" + "\n".join(f"- {task.title} [{CLEAN_TO_FRONTEND.get(task.status, task.status)}]" for task in tasks[:10])
        return {"response": response}
    return {"response": "Estoy conectado al backend limpio. Puedes pedirme ver tareas o agregar una foto."}
