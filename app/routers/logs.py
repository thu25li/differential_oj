from fastapi import APIRouter, Depends, Query
from app.models.common import ok
from app.services.log_service import log_service
from app.utils.auth import require_active, require_admin, require_teacher_or_admin
router = APIRouter(tags=["logs"])
@router.get("/api/submissions/{submission_id}/logs")
async def get_submission_logs(
    submission_id: str,
    user: dict = Depends(require_active),
):
    data = await log_service.get_logs_for_submission(submission_id, user)
    return ok(data=data)
@router.get("/api/logs")
async def list_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    submission_id: str | None = Query(default=None),
    problem_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    result: str | None = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    user: dict = Depends(require_teacher_or_admin),
):
    filters = {
        "page": page, "page_size": page_size,
        "submission_id": submission_id, "problem_id": problem_id,
        "user_id": user_id, "result": result,
        "start_time": start_time, "end_time": end_time,
    }
    data = await log_service.list_logs(filters, user)
    return ok(data=data)
@router.get("/api/audit-logs")
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    operator_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    target_id: str | None = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    user: dict = Depends(require_admin),
):
    filters = {
        "page": page, "page_size": page_size,
        "operator_id": operator_id, "action": action,
        "target_id": target_id,
        "start_time": start_time, "end_time": end_time,
    }
    data = await log_service.list_audit_logs(filters, user)
    return ok(data=data)
__all__ = ["router"]
