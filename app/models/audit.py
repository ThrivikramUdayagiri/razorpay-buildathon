from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class AuditLedger(Base):
    __tablename__ = "audit_ledger"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    entity_type = Column(String, index=True, nullable=False)
    entity_id = Column(String, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    decision = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    previous_hash = Column(String, nullable=True)
    record_hash = Column(String, nullable=False)

class NotificationEvent(Base):
    __tablename__ = "notification_events"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    recipient_reference = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    sent_at = Column(DateTime, server_default=func.now())
