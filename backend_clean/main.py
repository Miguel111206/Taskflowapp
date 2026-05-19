"""
TaskFlow - Task Management Application

A professional backend built with Clean Architecture.

Run with: uvicorn main:app --reload --host 127.0.0.1 --port 8010
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import models to register them with Base metadata
from src.infrastructure.models.user_model import UserModel
from src.infrastructure.models.task_model import TaskModel

from src.infrastructure.database.session import Base, engine, create_tables
from sqlalchemy import text
from src.presentation.api.endpoints import auth, compat, tasks


app = FastAPI(
    title="TaskFlow API",
    description="Professional task management application with Clean Architecture",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
async def startup():
    """Create tables on startup."""
    create_tables()
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
    return {
        "message": "Welcome to TaskFlow API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "database": "connected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8010)
