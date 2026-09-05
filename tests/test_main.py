import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.audit import AuditLedger
import json
import uuid
from scripts.run_demo import create_signature

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_invalid_signature(client):
    payload = {"event": "payment.failed", "payload": {}}
    headers = {"X-Razorpay-Signature": "invalid_sig"}
    response = client.post("/webhooks/razorpay", json=payload, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"

def test_duplicate_webhook_idempotency(client, db):
    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_" + str(uuid.uuid4())[:8],
                    "amount": 1000,
                    "currency": "INR",
                    "status": "failed",
                    "error_code": "BAD_REQUEST_ERROR"
                }
            }
        }
    }
    payload_str = json.dumps(payload, separators=(',', ':'))
    sig = create_signature(payload_str)
    event_id = "evt_" + str(uuid.uuid4())[:16]
    
    headers = {
        "X-Razorpay-Signature": sig,
        "X-Razorpay-Event-Id": event_id,
        "Content-Type": "application/json"
    }
    
    # First request
    r1 = client.post("/webhooks/razorpay", data=payload_str, headers=headers)
    assert r1.status_code == 200
    assert r1.json()["status"] == "processed"
    
    # Second request
    r2 = client.post("/webhooks/razorpay", data=payload_str, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["duplicate_event"] == True
    
    db.expire_all()
    # Verify audit log recorded duplicate block
    audit = db.query(AuditLedger).filter(
        AuditLedger.entity_id == event_id,
        AuditLedger.event_type == "WEBHOOK_DUPLICATE"
    ).first()
    assert audit is not None

def test_mandate_revoked_hard_stop(client, db):
    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_" + str(uuid.uuid4())[:8],
                    "subscription_id": "sub_test",
                    "amount": 1000,
                    "status": "failed",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "mandate revoked"
                }
            }
        }
    }
    payload_str = json.dumps(payload, separators=(',', ':'))
    sig = create_signature(payload_str)
    event_id = "evt_" + str(uuid.uuid4())[:16]
    
    headers = {
        "X-Razorpay-Signature": sig,
        "X-Razorpay-Event-Id": event_id,
        "Content-Type": "application/json"
    }
    
    r1 = client.post("/webhooks/razorpay", data=payload_str, headers=headers)
    assert r1.status_code == 200
    assert r1.json()["status"] == "processed_hard_stop"
    
    db.expire_all()
    # Verify policy denied it
    audit = db.query(AuditLedger).filter(
        AuditLedger.entity_id == event_id,
        AuditLedger.event_type == "POLICY_DENIED"
    ).first()
    assert audit is not None
    assert audit.reason == "MANDATE_REVOKED"
