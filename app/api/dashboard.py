from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.revenue_service import RevenueService
from app.services.ai_gatekeeper import AIGatekeeper
from app.models.audit import AuditLedger
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
ai_gatekeeper = AIGatekeeper()

from fastapi.responses import HTMLResponse, RedirectResponse

@router.get("/")
def read_root():
    return RedirectResponse(url="/demo/")

@router.get("/audit", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    metrics = RevenueService.calculate_metrics(db)
    recent_audits = db.query(AuditLedger).order_by(AuditLedger.id.desc()).limit(15).all()
    ai_provider = ai_gatekeeper.get_provider_info()
    
    # In a full app, we'd query specific counts for Engine A/B here.
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "metrics": metrics,
            "audits": recent_audits,
            "ai_provider": ai_provider
        }
    )
