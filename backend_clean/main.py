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
from src.presentation.api.endpoints import auth, tasks


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

app.include_router(auth.router)
app.include_router(tasks.router)


@app.on_event("startup")
async def startup():
    """Create tables on startup."""
    create_tables()


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