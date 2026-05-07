"""Pytest configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.database.base import Base


@pytest.fixture(scope="function")
def engine():
    """Create test database engine."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    return test_engine


@pytest.fixture(scope="function")
def session_factory(engine):
    """Create session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session(session_factory):
    """Create database session for testing."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()