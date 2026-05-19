from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from .endpoints import auth, compat, tasks
from src.infrastructure.database.base import Base
from src.infrastructure.database.engine import engine

app = FastAPI(
    title="TaskFlow API",
    description="Task management application with Clean Architecture",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compat.router)
app.include_router(auth.router)
app.include_router(tasks.router)


@app.on_event("startup")
async def on_startup():
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        task_columns = [row[1] for row in conn.execute(text("PRAGMA table_info(tasks)")).fetchall()]
        if "image" not in task_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN image TEXT"))
        user_columns = [row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
        user_column_defs = {
            "is_2fa_enabled": "BOOLEAN DEFAULT 0",
            "totp_secret": "VARCHAR(64)",
            "login_attempts": "INTEGER DEFAULT 0",
            "locked_until": "DATETIME",
        }
        for column, definition in user_column_defs.items():
            if column not in user_columns:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {column} {definition}"))


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "TaskFlow API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
