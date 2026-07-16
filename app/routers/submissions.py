from fastapi import APIRouter, Depends, Query
from app.models.common import accepted, ok
from app.models.submission import SubmissionCreate
from app.services.submission_service import submission_service
from app.utils.auth import require_active, require_teacher_or_admin
router = APIRouter(prefix="/api/submissions", tags=["submissions"])
@router.post("", status_code=202)
async def create_submission(
    body: SubmissionCreate,
    user: dict = Depends(require_active),
):
    data = await submission_service.create(body, user)
    return accepted(data=data, message="submission accepted")
@router.get("")
async def list_submissions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    problem_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    result: str | None = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    current_user: dict = Depends(require_active),
):
    filters = {
        "page": page, "page_size": page_size,
        "problem_id": problem_id, "user_id": user_id,
        "status": status, "result": result,
        "start_time": start_time, "end_time": end_time,
    }
    data = await submission_service.list(filters, current_user)
    return ok(data=data)
@router.get("/{submission_id}")
async def get_submission(
    submission_id: str,
    user: dict = Depends(require_active),
):
    data = await submission_service.get(submission_id, user)
    return ok(data=data)
@router.post("/{submission_id}/rejudge")
async def rejudge_submission(
    submission_id: str,
    user: dict = Depends(require_teacher_or_admin),
):
    data = await submission_service.rejudge(submission_id, user)
    return ok(data=data, message="rejudge scheduled")
__all__ = ["router"]