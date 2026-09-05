import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Boolean, JSON
from sqlalchemy.sql import func
from app.database import Base

class EventStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    DUPLICATE = "DUPLICATE"
    FAILED = "FAILED"

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    occurred_at = Column(DateTime, nullable=True)
    payload = Column(JSON, nullable=False)
    status = Column(Enum(EventStatus), default=EventStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())

class PaymentRecord(Base):
    __tablename__ = "payment_records"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, index=True, nullable=False)
    order_id = Column(String, index=True, nullable=True)
    subscription_id = Column(String, index=True, nullable=True)
    customer_id = Column(String, index=True, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    status = Column(String, index=True)
    failure_code = Column(String, nullable=True)
    failure_description = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
