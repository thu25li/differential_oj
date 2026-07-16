from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(tags=["pages"])
@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})
@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})
@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"request": request})
__all__ = ["router"]
