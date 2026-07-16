from fastapi import APIRouter, Depends, Query
from app.models.common import ok
from app.services.similarity_service import similarity_service
from app.utils.auth import require_teacher_or_admin
from app.utils.errors import NotFoundError
from app.repositories.problem_repository import problem_repository
router = APIRouter(tags=["similarity"])
@router.post("/api/problems/{problem_id}/similarity-check")
async def check_similarity(
    problem_id: str,
    threshold: float = Query(default=None, ge=0.0, le=1.0),
    user: dict = Depends(require_teacher_or_admin),
):
    if not await problem_repository.exists(problem_id):
        raise NotFoundError("problem not found")
    if threshold is None:
        data = await similarity_service.check(problem_id, user)
    else:
        data = await similarity_service.check(problem_id, user, threshold=threshold)
    return ok(data=data, message="similarity check completed")
@router.get("/api/problems/{problem_id}/similarity-reports")
async def list_similarity_reports(
    problem_id: str,
    user: dict = Depends(require_teacher_or_admin),
):
    if not await problem_repository.exists(problem_id):
        raise NotFoundError("problem not found")
    data = await similarity_service.list_reports(problem_id)
    return ok(data=data)
__all__ = ["router"]
