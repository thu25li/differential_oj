from typing import List
from app.models.problem import ProblemCreate, ProblemUpdate
from app.repositories.problem_repository import problem_repository
from app.utils.errors import ConflictError, NotFoundError, SystemError
from app.utils.time import now_utc
class ProblemService:
    async def list_problems(self, page: int = 1, page_size: int = 20) -> dict:
        items, total = await problem_repository.list(page=page, page_size=page_size)
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    async def get_problem(self, problem_id: str, include_test_cases: bool = False) -> dict:
        p = await problem_repository.get(problem_id)
        if p is None:
            raise NotFoundError("problem not found")
        if include_test_cases:
            p["test_cases"] = await problem_repository.get_test_cases(problem_id)
        return p
    async def create_problem(self, data: ProblemCreate) -> dict:
        if await problem_repository.exists(data.id):
            raise ConflictError(f"problem id '{data.id}' already exists")
        ts = now_utc()
        problem_dict = {
            "id": data.id,
            "title": data.title,
            "description": data.description,
            "input_description": data.input_description,
            "output_description": data.output_description,
            "samples": [s.model_dump() for s in data.samples],
            "constraints": data.constraints,
            "time_limit": data.time_limit,
            "memory_limit": data.memory_limit,
            "difficulty": data.difficulty.value,
            "tags": data.tags,
            "created_at": ts,
            "updated_at": ts,
        }
        test_cases = [tc.model_dump() for tc in data.test_cases]
        try:
            await problem_repository.create(problem_dict, test_cases)
        except Exception as e:
            raise SystemError("failed to create problem") from e
        result = dict(problem_dict)
        result["test_cases"] = test_cases
        return result
    async def update_problem(self, problem_id: str, data: ProblemUpdate) -> dict:
        if not await problem_repository.exists(problem_id):
            raise NotFoundError("problem not found")
        ts = now_utc()
        problem_dict = {
            "title": data.title,
            "description": data.description,
            "input_description": data.input_description,
            "output_description": data.output_description,
            "samples": [s.model_dump() for s in data.samples],
            "constraints": data.constraints,
            "time_limit": data.time_limit,
            "memory_limit": data.memory_limit,
            "difficulty": data.difficulty.value,
            "tags": data.tags,
            "updated_at": ts,
        }
        test_cases = [tc.model_dump() for tc in data.test_cases]
        ok = await problem_repository.update(problem_id, problem_dict, test_cases)
        if not ok:
            raise NotFoundError("problem not found")
        updated = await problem_repository.get(problem_id)
        updated["test_cases"] = await problem_repository.get_test_cases(problem_id)
        return updated
    async def delete_problem(self, problem_id: str) -> None:
        if not await problem_repository.exists(problem_id):
            raise NotFoundError("problem not found")
        ok = await problem_repository.delete(problem_id)
        if not ok:
            raise NotFoundError("problem not found")
problem_service = ProblemService()