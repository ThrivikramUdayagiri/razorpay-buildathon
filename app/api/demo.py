from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.demo_state import demo_state

router = APIRouter(prefix="/demo", tags=["demo"])
templates = Jinja2Templates(directory="app/templates")

class ProbabilityRequest(BaseModel):
    probability: int

class ActionRequest(BaseModel):
    user_id: int
    action: str

@router.get("/", response_class=HTMLResponse)
async def demo_arena(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="demo.html",
        context={"request": request}
    )

@router.get("/api/state")
def get_state():
    return demo_state.get_state()

@router.post("/api/set-probability")
def set_probability(req: ProbabilityRequest):
    demo_state.set_probability(req.probability)
    return {"status": "success", "probability": demo_state.global_probability}

@router.post("/api/user-action")
def user_action(req: ActionRequest):
    success = demo_state.user_action(req.user_id, req.action)
    return {"status": "success" if success else "error"}

@router.post("/api/reset")
def reset_demo():
    demo_state.reset()
    return {"status": "success"}
