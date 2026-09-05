from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.recovery import RecoverySession, RecoverySessionStatus
from app.models.cart import Cart, CartItem
from app.models.payment import PaymentRecord
from app.integrations import get_razorpay_adapter
from app.services.audit_service import AuditService

router = APIRouter()

@router.get("/pay/resume", response_class=HTMLResponse)
def resume_payment(token: str, db: Session = Depends(get_db)):
    """
    Tokenized resume flow for Engine B.
    """
    import hashlib
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    session = db.query(RecoverySession).filter(RecoverySession.token_hash == token_hash).first()
    if not session:
        return "<h1>Invalid Recovery Link</h1>"
        
    AuditService.log_event(db, "RecoverySession", str(session.id), "RECOVERY_SESSION_VALIDATED", "TOKEN_MATCHED")

    if session.status != RecoverySessionStatus.ACTIVE:
        return f"<h1>Recovery Session is {session.status.value}</h1>"
        
    if session.expires_at < datetime.utcnow():
        session.status = RecoverySessionStatus.EXPIRED
        db.commit()
        return "<h1>Link Expired</h1>"

    # Check if already paid
    if session.original_order_id:
        paid = db.query(PaymentRecord).filter(
            PaymentRecord.order_id == session.original_order_id,
            PaymentRecord.status.in_(["authorized", "captured"])
        ).first()
        if paid:
            session.status = RecoverySessionStatus.PAID
            db.commit()
            AuditService.log_event(db, "RecoverySession", str(session.id), "HARD_STOP", "ALREADY_PAID")
            return "<h1>Payment Already Completed. Thank you!</h1>"

    # Fetch current cart state (Simulated here if no cart_id exists, 
    # but we'll assume it exists if it's a real system)
    cart = db.query(Cart).filter(Cart.id == session.cart_id).first()
    
    current_amount = session.original_amount
    if cart:
        items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        if not items:
            session.status = RecoverySessionStatus.INVALIDATED
            db.commit()
            AuditService.log_event(db, "RecoverySession", str(session.id), "HARD_STOP", "CART_EMPTY")
            return "<h1>Your cart is empty. Recovery unavailable.</h1>"
            
        current_amount = sum(item.price * item.quantity for item in items)
        
        if current_amount != session.current_amount:
            AuditService.log_event(
                db, "RecoverySession", str(session.id), "CART_RECALCULATED", "AMOUNT_CHANGED",
                metadata={"old": session.current_amount, "new": current_amount}
            )
            session.current_amount = current_amount
            db.commit()

    # Create fresh order with the current amount
    adapter = get_razorpay_adapter()
    new_order = adapter.create_order(amount=current_amount, receipt=f"resume_{session.id}")
    
    AuditService.log_event(db, "RecoverySession", str(session.id), "ORDER_CREATED", metadata={"new_order_id": new_order["id"]})

    # Return a basic checkout page
    html = f"""
    <html>
        <head><title>Complete Payment</title></head>
        <body style="font-family: sans-serif; padding: 2rem;">
            <h2>Complete your purchase</h2>
            <p>Original Amount: ₹{session.original_amount}</p>
            <p><strong>Current Amount to Pay: ₹{current_amount}</strong></p>
            <button style="padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer;">
                Pay Now (Order ID: {new_order["id"]})
            </button>
            <p style="color: #666; font-size: 0.8rem; margin-top: 1rem;">
                This is a simulated checkout page.
            </p>
        </body>
    </html>
    """
    return html
