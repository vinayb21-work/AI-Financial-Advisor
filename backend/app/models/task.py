from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum
from app.core.database import Base

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="SET NULL"))
    
    description = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    
    # Task execution data
    context = Column(JSONB)  # Context needed to complete the task
    steps = Column(JSONB)  # Steps completed so far
    next_action = Column(Text)  # What needs to happen next
    waiting_for = Column(String)  # What the task is waiting for (e.g., "email response")
    
    # Results
    result = Column(Text)
    error = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Task {self.description[:50]} - {self.status}>"

