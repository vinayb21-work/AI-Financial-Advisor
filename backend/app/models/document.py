from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Document metadata
    source = Column(String, nullable=False)  # "gmail", "hubspot_contact", "hubspot_note"
    source_id = Column(String, nullable=False)  # External ID from the source
    document_type = Column(String)
    
    # Content
    content = Column(Text, nullable=False)
    title = Column(String)
    
    # Vector embedding (1536 dimensions for OpenAI embeddings)
    embedding = Column(Vector(1536))
    
    # Additional metadata
    doc_metadata = Column(Text)  # JSON string with extra info
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Document {self.source} - {self.title}>"

