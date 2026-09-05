import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class RecoverySessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"
    PAID = "PAID"
    RECOVERED = "RECOVERED"

class RecoveryAttemptStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class RecoverySession(Base):
    __tablename__ = "recovery_sessions"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(String, index=True, nullable=False)
    cart_id = Column(String, nullable=True)
    original_order_id = Column(String, index=True, nullable=True)
    original_amount = Column(Float, nullable=False)
    current_amount = Column(Float, nullable=False)
    status = Column(Enum(RecoverySessionStatus), default=RecoverySessionStatus.ACTIVE)
    touch_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)

class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(String, index=True, nullable=True)
    customer_id = Column(String, index=True, nullable=True)
    attempt_number = Column(Integer, default=1)
    reason = Column(String, nullable=False)
    status = Column(Enum(RecoveryAttemptStatus), default=RecoveryAttemptStatus.SCHEDULED)
    scheduled_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
