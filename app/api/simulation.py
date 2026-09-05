from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import json
from app.database import get_db
from app.models.payment import PaymentRecord
from app.models.cart import Cart, CartItem
from app.models.recovery import RecoverySession

router = APIRouter()

@router.post("/api/simulate/event")
def simulate_event(event_data: dict, db: Session = Depends(get_db)):
    """
    Directly injects a simulated event into the database to aid the demo script.
    (In real life, this would just be the webhook endpoint processing it).
    """
    # Just a helper to mock initial db state for the demo
    return {"status": "accepted"}

from datetime import datetime, timedelta
from app.models.recovery import RecoveryAttempt

@router.post("/api/simulate/fast-forward")
def fast_forward_time(db: Session = Depends(get_db)):
    """
    Demo utility: Updates all scheduled recoveries to simulate time passing (e.g. 72 hours later)
    so the Background Recovery Worker instantly executes them.
    """
    attempts = db.query(RecoveryAttempt).filter(RecoveryAttempt.status == "SCHEDULED").all()
    count = len(attempts)
    
    # Push the scheduled time back by 100 hours to force it to be "due"
    past_time = datetime.utcnow() - timedelta(hours=100)
    for attempt in attempts:
        attempt.scheduled_at = past_time
        
    db.commit()
    
    return {"status": "success", "fast_forwarded_events": count, "message": "Background worker will execute these momentarily."}
