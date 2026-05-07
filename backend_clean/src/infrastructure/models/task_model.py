from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from datetime import datetime
import uuid
from src.infrastructure.database.session import Base


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
    
    def __repr__(self):
        return f"<TaskModel(title='{self.title}', status='{self.status}')>"