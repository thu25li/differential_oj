from typing import List, Optional, Tuple
from app.database import get_db
class CaseLogRepository:
    async def create_batch(self, case_logs: List[dict]) -> None:
        if not case_logs:
            return
        db = await get_db()
        try:
            for log in case_logs:
                await db.execute(
                    """INSERT INTO case_logs
                       (submission_id, case_id, result, score, time_used, memory_used,
                        exit_code, input_data, stdout, stderr, expected_output,
                        message, is_hidden, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        log["submission_id"], log["case_id"], log["result"],
                        log["score"], log["time_used"], log.get("memory_used"),
                        log.get("exit_code"), log.get("input_data"),
                        log.get("stdout"), log.get("stderr"),
                        log.get("expected_output"), log.get("message"),
                        1 if log.get("is_hidden") else 0, log["created_at"],
                    ),
                )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    async def get_by_submission(self, submission_id: str) -> List[dict]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT submission_id, case_id, result, score, time_used, memory_used,
                      exit_code, input_data, stdout, stderr, expected_output,
                      message, is_hidden, created_at
               FROM case_logs WHERE submission_id = ?
               ORDER BY id""",
            (submission_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_dict(r) for r in rows]
    async def delete_by_submission(self, submission_id: str) -> int:
        db = await get_db()
        try:
            cursor = await db.execute(
                "DELETE FROM case_logs WHERE submission_id = ?",
                (submission_id,),
            )
            await db.commit()
            return cursor.rowcount
        except Exception:
            await db.rollback()
            raise
    async def list(
        self,
        page: int = 1, page_size: int = 20,
        submission_id: Optional[str] = None,
        problem_id: Optional[str] = None,
        user_id: Optional[str] = None,
        result: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        db = await get_db()
        where_parts: List[str] = []
        params: List = []
        if submission_id is not None:
            where_parts.append("cl.submission_id = ?")
            params.append(submission_id)
        if problem_id is not None:
            where_parts.append("s.problem_id = ?")
            params.append(problem_id)
        if user_id is not None:
            where_parts.append("s.user_id = ?")
            params.append(user_id)
        if result is not None:
            where_parts.append("cl.result = ?")
            params.append(result)
        if start_time is not None:
            where_parts.append("cl.created_at >= ?")
            params.append(start_time)
        if end_time is not None:
            where_parts.append("cl.created_at <= ?")
            params.append(end_time)
        where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
        offset = (page - 1) * page_size
        cursor = await db.execute(
            f"""SELECT cl.submission_id, cl.case_id, cl.result, cl.score, cl.time_used,
                       cl.memory_used, cl.exit_code, cl.input_data, cl.stdout, cl.stderr,
                       cl.expected_output, cl.message, cl.is_hidden, cl.created_at
                FROM case_logs cl
                JOIN submissions s ON cl.submission_id = s.id
                {where_clause}
                ORDER BY cl.created_at DESC, cl.id DESC
                LIMIT ? OFFSET ?""",
            params + [page_size, offset],
        )
        rows = await cursor.fetchall()
        items = [self._row_to_dict(r) for r in rows]
        cursor = await db.execute(
            f"""SELECT COUNT(*) FROM case_logs cl
                JOIN submissions s ON cl.submission_id = s.id
                {where_clause}""",
            params,
        )
        total = (await cursor.fetchone())[0]
        return items, total
    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "submission_id": row["submission_id"],
            "case_id": row["case_id"],
            "result": row["result"],
            "score": row["score"],
            "time_used": row["time_used"],
            "memory_used": row["memory_used"],
            "exit_code": row["exit_code"],
            "input_data": row["input_data"],
            "stdout": row["stdout"],
            "stderr": row["stderr"],
            "expected_output": row["expected_output"],
            "message": row["message"],
            "is_hidden": bool(row["is_hidden"]),
            "created_at": row["created_at"],
        }
case_log_repository = CaseLogRepository()
