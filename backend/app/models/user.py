from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    picture = Column(String)
    
    # Google OAuth tokens
    google_access_token = Column(Text)
    google_refresh_token = Column(Text)
    google_token_expiry = Column(DateTime)
    
    # Hubspot OAuth tokens
    hubspot_access_token = Column(Text)
    hubspot_refresh_token = Column(Text)
    hubspot_token_expiry = Column(DateTime)
    hubspot_connected = Column(Boolean, default=False)
    
    # Sync status
    gmail_synced = Column(Boolean, default=False)
    calendar_synced = Column(Boolean, default=False)
    hubspot_synced = Column(Boolean, default=False)
    last_gmail_sync = Column(DateTime)
    last_calendar_sync = Column(DateTime)
    last_hubspot_sync = Column(DateTime)
    last_gmail_check = Column(DateTime)  # For polling new emails
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.email}>"

