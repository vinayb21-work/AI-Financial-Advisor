from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime

class WebhookSubscription(Base):
    """Model for tracking webhook subscriptions"""
    __tablename__ = "webhook_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Subscription details
    service = Column(String, nullable=False)  # 'gmail', 'calendar', 'hubspot'
    resource_id = Column(String, nullable=False)  # Google resource ID or Hubspot subscription ID
    channel_id = Column(String, nullable=False)  # Unique channel ID
    
    # Expiration
    expiration = Column(DateTime, nullable=True)  # When the subscription expires
    
    # Status
    active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

