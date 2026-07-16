from fastapi import APIRouter, Depends, Query
from app.models.common import PageParams, created, ok
from app.models.problem import ProblemCreate, ProblemUpdate
from app.services.problem_service import problem_service
from app.utils.auth import require_active, require_teacher_or_admin
router = APIRouter(prefix="/api/problems", tags=["problems"])
@router.get("")
async def list_problems(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(require_active),
):
    data = await problem_service.list_problems(page=page, page_size=page_size)
    return ok(data=data)
@router.get("/{problem_id}")
async def get_problem(
    problem_id: str,
    user: dict = Depends(require_active),
):
    include_test_cases = user["role"] in ("teacher", "admin")
    data = await problem_service.get_problem(
        problem_id, include_test_cases=include_test_cases
    )
    return ok(data=data)
@router.post("", status_code=201)
async def create_problem(
    body: ProblemCreate,
    user: dict = Depends(require_teacher_or_admin),
):
    data = await problem_service.create_problem(body)
    return created(data=data, message="problem created")
@router.put("/{problem_id}")
async def update_problem(
    problem_id: str,
    body: ProblemUpdate,
    user: dict = Depends(require_teacher_or_admin),
):
    data = await problem_service.update_problem(problem_id, body)
    return ok(data=data, message="problem updated")
@router.delete("/{problem_id}")
async def delete_problem(
    problem_id: str,
    user: dict = Depends(require_teacher_or_admin),
):
    await problem_service.delete_problem(problem_id)
    return ok(data=None, message="problem deleted")
__all__ = ["router"]