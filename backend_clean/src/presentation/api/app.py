from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import auth, tasks
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

app.include_router(auth.router)
app.include_router(tasks.router)


@app.on_event("startup")
async def on_startup():
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "TaskFlow API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}