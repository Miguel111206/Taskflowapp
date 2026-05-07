from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator

SQLALCHEMY_DATABASE_URL = "sqlite:///./taskflow.db"

metadata = MetaData()

Base = declarative_base(metadata=metadata)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_tables() -> None:
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session."""
    return get_session