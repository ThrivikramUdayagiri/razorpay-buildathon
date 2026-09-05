from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.audit_service import AuditService
from app.models.audit import AuditLedger

router = APIRouter()

@router.get("/api/audit")
def get_audit_trail(db: Session = Depends(get_db)):
    records = db.query(AuditLedger).order_by(AuditLedger.id.desc()).limit(100).all()
    return records

@router.get("/audit/verify")
def verify_audit_chain(db: Session = Depends(get_db)):
    """
    Verifies the hash chain of the audit ledger.
    """
    result = AuditService.verify_chain(db)
    return result
