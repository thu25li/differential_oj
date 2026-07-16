from typing import List, Optional, Tuple
from app.database import get_db
class SubmissionRepository:
    async def create(self, sub: dict) -> None:
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO submissions
                   (id, user_id, problem_id, language, source_code,
                    status, result, score, total_time,
                    created_at, started_at, finished_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sub["id"], sub["user_id"], sub["problem_id"],
                    sub["language"], sub["source_code"],
                    sub["status"], None,
                    0, None,
                    sub["created_at"], None, None,
                ),
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    async def get_by_id(self, submission_id: str) -> Optional[dict]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT id, user_id, problem_id, language, source_code,
                      status, result, score, total_time,
                      created_at, started_at, finished_at
               FROM submissions WHERE id = ?""",
            (submission_id,),
        )
        row = await cursor.fetchone()
        return self._row_to_dict(row) if row else None
    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        problem_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        result: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        db = await get_db()
        where_parts: List[str] = []
        params: List = []
        if problem_id is not None:
            where_parts.append("problem_id = ?")
            params.append(problem_id)
        if user_id is not None:
            where_parts.append("user_id = ?")
            params.append(user_id)
        if status is not None:
            where_parts.append("status = ?")
            params.append(status)
        if result is not None:
            where_parts.append("result = ?")
            params.append(result)
        if start_time is not None:
            where_parts.append("created_at >= ?")
            params.append(start_time)
        if end_time is not None:
            where_parts.append("created_at <= ?")
            params.append(end_time)
        where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
        offset = (page - 1) * page_size
        cursor = await db.execute(
            f"""SELECT id, user_id, problem_id, language, status, result,
                       score, total_time, created_at, started_at, finished_at
                FROM submissions{where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?""",
            params + [page_size, offset],
        )
        rows = await cursor.fetchall()
        items = [self._row_to_dict(row, include_source=False) for row in rows]
        cursor = await db.execute(
            f"SELECT COUNT(*) FROM submissions{where_clause}", params
        )
        total = (await cursor.fetchone())[0]
        return items, total
    async def update_status(
        self,
        submission_id: str,
        status: str,
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
    ) -> bool:
        db = await get_db()
        set_parts: List[str] = ["status = ?"]
        params: List = [status]
        if started_at is not None:
            set_parts.append("started_at = ?")
            params.append(started_at)
        if finished_at is not None:
            set_parts.append("finished_at = ?")
            params.append(finished_at)
        params.append(submission_id)
        try:
            cursor = await db.execute(
                f"UPDATE submissions SET {', '.join(set_parts)} WHERE id = ?",
                params,
            )
            if cursor.rowcount == 0:
                await db.rollback()
                return False
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            raise
    async def update_result(
        self,
        submission_id: str,
        result: str,
        score: int,
        total_time: float,
        finished_at: str,
    ) -> bool:
        db = await get_db()
        final_status = "failed" if result == "SE" else "finished"
        try:
            cursor = await db.execute(
                """UPDATE submissions
                   SET status = ?, result = ?, score = ?,
                       total_time = ?, finished_at = ?
                   WHERE id = ?""",
                (final_status, result, score, total_time, finished_at, submission_id),
            )
            if cursor.rowcount == 0:
                await db.rollback()
                return False
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            raise
    async def reset_for_rejudge(self, submission_id: str) -> bool:
        db = await get_db()
        try:
            cursor = await db.execute(
                """UPDATE submissions
                   SET status = 'pending', result = NULL, score = 0,
                       total_time = NULL, started_at = NULL, finished_at = NULL
                   WHERE id = ?""",
                (submission_id,),
            )
            if cursor.rowcount == 0:
                await db.rollback()
                return False
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            raise
    async def exists(self, submission_id: str) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "SELECT 1 FROM submissions WHERE id = ?", (submission_id,)
        )
        return await cursor.fetchone() is not None
    async def list_sources_by_problem(self, problem_id: str) -> List[dict]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT id, user_id, source_code FROM submissions
               WHERE problem_id = ? AND status IN ('finished', 'failed')
               ORDER BY id""",
            (problem_id,),
        )
        rows = await cursor.fetchall()
        return [
            {"id": r["id"], "user_id": r["user_id"], "source_code": r["source_code"]}
            for r in rows
        ]
    @staticmethod
    def _row_to_dict(row, include_source: bool = True) -> dict:
        d = {
            "id": row["id"],
            "user_id": row["user_id"],
            "problem_id": row["problem_id"],
            "language": row["language"],
            "status": row["status"],
            "result": row["result"],
            "score": row["score"],
            "total_time": row["total_time"],
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
        }
        if include_source:
            d["source_code"] = row["source_code"]
        return d
submission_repository = SubmissionRepository()