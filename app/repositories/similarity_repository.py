from typing import List, Optional, Tuple
from app.database import get_db
class SimilarityRepository:
    async def create_batch(self, reports: List[dict]) -> None:
        if not reports:
            return
        db = await get_db()
        try:
            for r in reports:
                await db.execute(
                    """INSERT INTO similarity_reports
                       (problem_id, submission_a, submission_b, similarity, method, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        r["problem_id"], r["submission_a"], r["submission_b"],
                        r["similarity"], r.get("method", "ast"), r["created_at"],
                    ),
                )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    async def delete_by_problem(self, problem_id: str) -> int:
        db = await get_db()
        try:
            cursor = await db.execute(
                "DELETE FROM similarity_reports WHERE problem_id = ?",
                (problem_id,),
            )
            await db.commit()
            return cursor.rowcount
        except Exception:
            await db.rollback()
            raise
    async def list_by_problem(self, problem_id: str) -> List[dict]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT id, problem_id, submission_a, submission_b, similarity,
                      method, created_at
               FROM similarity_reports WHERE problem_id = ?
               ORDER BY similarity DESC, created_at DESC""",
            (problem_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r["id"],
                "problem_id": r["problem_id"],
                "submission_a": r["submission_a"],
                "submission_b": r["submission_b"],
                "similarity": r["similarity"],
                "method": r["method"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
similarity_repository = SimilarityRepository()
