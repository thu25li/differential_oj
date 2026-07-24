from app.repositories.audit_log_repository import audit_log_repository
from app.repositories.case_log_repository import case_log_repository
from app.repositories.submission_repository import submission_repository
from app.utils.errors import ForbiddenError, NotFoundError
from app.utils.id_gen import generate_uuid
from app.utils.log_views import to_student_log_view, to_teacher_log_view
from app.utils.time import now_utc
class LogService:
    async def get_logs_for_submission(self, submission_id: str, current_user: dict) -> dict:
        sub = await submission_repository.get_by_id(submission_id)
        if sub is None:
            raise NotFoundError("submission not found")
        role = current_user["role"]
        if role == "student" and sub["user_id"] != current_user["id"]:
            raise ForbiddenError("cannot view others' submissions")
        logs = await case_log_repository.get_by_submission(submission_id)
        if role == "student":
            cases = [to_student_log_view(log) for log in logs]
        else:
            cases = [to_teacher_log_view(log) for log in logs]
            await audit_log_repository.create({
                "id": generate_uuid(),
                "operator_id": current_user["id"],
                "action": "VIEW_FULL_JUDGE_LOG",
                "target_type": "submission",
                "target_id": submission_id,
                "success": True,
                "detail": None,
                "created_at": now_utc(),
            })
        return {"submission_id": submission_id, "cases": cases}
    async def list_logs(self, filters: dict, current_user: dict) -> dict:
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        items, total = await case_log_repository.list(
            page=page, page_size=page_size,
            submission_id=filters.get("submission_id"),
            problem_id=filters.get("problem_id"),
            user_id=filters.get("user_id"),
            result=filters.get("result"),
            start_time=filters.get("start_time"),
            end_time=filters.get("end_time"),
        )
        view = [to_teacher_log_view(item) for item in items]
        return {"items": view, "total": total, "page": page, "page_size": page_size}
    async def list_audit_logs(self, filters: dict, current_user: dict) -> dict:
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        items, total = await audit_log_repository.list(
            page=page, page_size=page_size,
            operator_id=filters.get("operator_id"),
            operator_username=filters.get("operator_username"),
            action=filters.get("action"),
            target_id=filters.get("target_id"),
            start_time=filters.get("start_time"),
            end_time=filters.get("end_time"),
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}
log_service = LogService()
