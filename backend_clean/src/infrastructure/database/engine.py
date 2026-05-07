from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./taskflow.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,
    echo=False
)


def get_engine():
    """Get the database engine."""
    return engine