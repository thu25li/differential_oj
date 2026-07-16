import asyncio
import logging
from app.models.submission import SubmissionCreate
from app.repositories.audit_log_repository import audit_log_repository
from app.repositories.case_log_repository import case_log_repository
from app.repositories.problem_repository import problem_repository
from app.repositories.submission_repository import submission_repository
from app.utils.errors import (
    BadRequestError, ConflictError, ForbiddenError, NotFoundError,
)
from app.utils.id_gen import generate_uuid
from app.utils.log_utils import truncate_text
from app.utils.time import now_utc
logger = logging.getLogger(__name__)
_pending_tasks: set = set()
class SubmissionService:
    async def create(self, data: SubmissionCreate, current_user: dict) -> dict:
        if not await problem_repository.exists(data.problem_id):
            raise NotFoundError("problem not found")
        if data.language != "python":
            raise BadRequestError("only python language is supported in basic module")
        ts = now_utc()
        sub_id = generate_uuid()
        sub = {
            "id": sub_id,
            "user_id": current_user["id"],
            "problem_id": data.problem_id,
            "language": data.language,
            "source_code": data.source_code,
            "status": "pending",
            "created_at": ts,
        }
        await submission_repository.create(sub)
        self._schedule_judging(sub_id)
        return {"submission_id": sub_id, "status": "pending"}
    async def get(self, submission_id: str, current_user: dict) -> dict:
        sub = await submission_repository.get_by_id(submission_id)
        if sub is None:
            raise NotFoundError("submission not found")
        if current_user["role"] == "student" and sub["user_id"] != current_user["id"]:
            raise ForbiddenError("cannot view others' submissions")
        return sub
    async def list(self, filters: dict, current_user: dict) -> dict:
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        if current_user["role"] == "student":
            filters["user_id"] = current_user["id"]
        items, total = await submission_repository.list(
            page=page, page_size=page_size,
            problem_id=filters.get("problem_id"),
            user_id=filters.get("user_id"),
            status=filters.get("status"),
            result=filters.get("result"),
            start_time=filters.get("start_time"),
            end_time=filters.get("end_time"),
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    async def rejudge(self, submission_id: str, current_user: dict) -> dict:
        sub = await submission_repository.get_by_id(submission_id)
        if sub is None:
            raise NotFoundError("submission not found")
        if sub["status"] not in ("finished", "failed"):
            raise ConflictError("can only rejudge finished or failed submissions")
        ok = await submission_repository.reset_for_rejudge(submission_id)
        if not ok:
            raise NotFoundError("submission not found")
        await case_log_repository.delete_by_submission(submission_id)
        await audit_log_repository.create({
            "id": generate_uuid(),
            "operator_id": current_user["id"],
            "action": "REJUDGE_SUBMISSION",
            "target_type": "submission",
            "target_id": submission_id,
            "success": True,
            "detail": None,
            "created_at": now_utc(),
        })
        self._schedule_judging(submission_id)
        return {"submission_id": submission_id, "status": "pending"}
    def _schedule_judging(self, submission_id: str) -> None:
        task = asyncio.create_task(self._run_judging(submission_id))
        _pending_tasks.add(task)
        task.add_done_callback(_pending_tasks.discard)
    async def _run_judging(self, submission_id: str) -> None:
        from app.judge.judge import judge_submission
        try:
            sub = await submission_repository.get_by_id(submission_id)
            if sub is None:
                logger.error("submission %s not found during judging", submission_id)
                return
            await submission_repository.update_status(
                submission_id, "running", started_at=now_utc()
            )
            problem = await problem_repository.get(sub["problem_id"])
            if problem is None:
                await submission_repository.update_result(
                    submission_id, "SE", 0, 0.0, now_utc()
                )
                return
            test_cases = await problem_repository.get_test_cases(sub["problem_id"])
            result = await judge_submission(
                source_code=sub["source_code"],
                test_cases=test_cases,
                time_limit=problem["time_limit"],
            )
            await submission_repository.update_result(
                submission_id,
                result=result.final_result,
                score=result.total_score,
                total_time=result.total_time,
                finished_at=now_utc(),
            )
            ts = now_utc()
            case_logs = [
                {
                    "submission_id": submission_id,
                    "case_id": cr.case_id,
                    "result": cr.result,
                    "score": cr.score,
                    "time_used": cr.time_used,
                    "memory_used": None,
                    "exit_code": cr.exit_code,
                    "input_data": truncate_text(cr.input_data),
                    "stdout": truncate_text(cr.stdout),
                    "stderr": truncate_text(cr.stderr),
                    "expected_output": truncate_text(cr.expected_output),
                    "message": cr.message,
                    "is_hidden": cr.is_hidden,
                    "created_at": ts,
                }
                for cr in result.cases
            ]
            await case_log_repository.create_batch(case_logs)
        except Exception:
            logger.exception("judging failed for submission %s", submission_id)
            try:
                await submission_repository.update_result(
                    submission_id, "SE", 0, 0.0, now_utc()
                )
            except Exception:
                logger.exception(
                    "failed to mark submission %s as SE after judging error",
                    submission_id,
                )
submission_service = SubmissionService()
