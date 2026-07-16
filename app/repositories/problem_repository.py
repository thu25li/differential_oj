import json
from typing import List, Optional, Tuple
from app.database import get_db
class ProblemRepository:
    async def list(self, page: int = 1, page_size: int = 20) -> Tuple[List[dict], int]:
        db = await get_db()
        offset = (page - 1) * page_size
        cursor = await db.execute(
            """SELECT id, title, difficulty, tags, time_limit, memory_limit
               FROM problems ORDER BY id LIMIT ? OFFSET ?""",
            (page_size, offset),
        )
        rows = await cursor.fetchall()
        items = [
            {
                "id": r["id"],
                "title": r["title"],
                "difficulty": r["difficulty"],
                "tags": json.loads(r["tags"]) if r["tags"] else [],
                "time_limit": r["time_limit"],
                "memory_limit": r["memory_limit"],
            }
            for r in rows
        ]
        cursor = await db.execute("SELECT COUNT(*) FROM problems")
        total = (await cursor.fetchone())[0]
        return items, total
    async def get(self, problem_id: str) -> Optional[dict]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT id, title, description, input_description, output_description,
                      samples, constraints, time_limit, memory_limit, difficulty, tags
               FROM problems WHERE id = ?""",
            (problem_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        d = dict(row)
        d["samples"] = json.loads(d["samples"])
        d["tags"] = json.loads(d["tags"]) if d["tags"] else []
        d["constraints"] = d.get("constraints")
        return d
    async def get_test_cases(self, problem_id: str) -> List[dict]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT case_id, input, output, score, is_hidden
               FROM test_cases WHERE problem_id = ? ORDER BY id""",
            (problem_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "case_id": r["case_id"],
                "input": r["input"],
                "output": r["output"],
                "score": r["score"],
                "is_hidden": bool(r["is_hidden"]),
            }
            for r in rows
        ]
    async def exists(self, problem_id: str) -> bool:
        db = await get_db()
        cursor = await db.execute("SELECT 1 FROM problems WHERE id = ?",(problem_id,))
        return await cursor.fetchone() is not None
    async def create(self, problem: dict, test_cases: List[dict]) -> None:
        db = await get_db()
        ts = problem["created_at"]
        try:
            await db.execute(
                """INSERT INTO problems
                   (id, title, description, input_description, output_description,
                    samples, constraints, time_limit, memory_limit, difficulty,
                    tags, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    problem["id"], problem["title"], problem["description"],
                    problem["input_description"], problem["output_description"],
                    json.dumps(problem["samples"]), problem.get("constraints"),
                    problem["time_limit"], problem["memory_limit"], problem["difficulty"],
                    json.dumps(problem["tags"]), ts, ts,
                ),
            )
            for tc in test_cases:
                await db.execute(
                    """INSERT INTO test_cases
                       (case_id, problem_id, input, output, score, is_hidden, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        tc["case_id"], problem["id"], tc["input"], tc["output"],
                        tc["score"], 1 if tc["is_hidden"] else 0, ts,
                    ),
                )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    async def update(self, problem_id: str, problem: dict, test_cases: List[dict]) ->bool:
        db = await get_db()
        ts = problem["updated_at"]
        try:
            cursor = await db.execute(
                """UPDATE problems
                   SET title = ?, description = ?, input_description = ?,
                       output_description = ?, samples = ?, constraints = ?,
                       time_limit = ?, memory_limit = ?, difficulty = ?,
                       tags = ?, updated_at = ?
                   WHERE id = ?""",
                (
                    problem["title"], problem["description"], problem["input_description"],
                    problem["output_description"], json.dumps(problem["samples"]),
                    problem.get("constraints"), problem["time_limit"], problem["memory_limit"],
                    problem["difficulty"], json.dumps(problem["tags"]), ts, problem_id,
                ),
            )
            if cursor.rowcount == 0:
                await db.rollback()
                return False
            await db.execute("DELETE FROM test_cases WHERE problem_id = ?", (problem_id,))
            for tc in test_cases:
                await db.execute(
                    """INSERT INTO test_cases
                       (case_id, problem_id, input, output, score, is_hidden, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        tc["case_id"], problem_id, tc["input"], tc["output"],
                        tc["score"], 1 if tc["is_hidden"] else 0, ts,
                    ),
                )
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            raise
    async def delete(self, problem_id: str) -> bool:
        db = await get_db()
        cursor = await db.execute("DELETE FROM problems WHERE id = ?", (problem_id,))
        await db.commit()
        return cursor.rowcount > 0
problem_repository = ProblemRepository()