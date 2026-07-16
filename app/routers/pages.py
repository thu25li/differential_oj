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
@router.get("/problems")
async def problems_page(request: Request):
    return templates.TemplateResponse(request, "problems.html", {"request": request})
@router.get("/problems/{problem_id}")
async def problem_detail_page(request: Request, problem_id: str):
    return templates.TemplateResponse(request, "problem_detail.html", {"request": request, "problem_id": problem_id})
@router.get("/submissions")
async def submissions_page(request: Request):
    return templates.TemplateResponse(request, "submissions.html", {"request": request})
@router.get("/submissions/{submission_id}")
async def submission_detail_page(request: Request, submission_id: str):
    return templates.TemplateResponse(request, "submission_detail.html", {"request": request, "submission_id": submission_id})
@router.get("/teacher/problems")
async def teacher_problems_page(request: Request):
    return templates.TemplateResponse(request, "teacher_problems.html", {"request": request})
@router.get("/teacher/problems/new")
async def teacher_problem_new_page(request: Request):
    return templates.TemplateResponse(request, "teacher_problem_form.html", {"request": request, "mode": "create", "problem_id": ""})
@router.get("/teacher/problems/{problem_id}/edit")
async def teacher_problem_edit_page(request: Request, problem_id: str):
    return templates.TemplateResponse(request, "teacher_problem_form.html", {"request": request, "mode": "edit", "problem_id": problem_id})
@router.get("/admin/backups")
async def admin_backups_page(request: Request):
    return templates.TemplateResponse(request, "admin_backups.html", {"request": request})
__all__ = ["router"]
