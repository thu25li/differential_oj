import pytest

from app.repositories.problem_repository import problem_repository
from app.utils.time import now_utc


def _make_problem(pid="P1001"):
    return {
        "id": pid,
        "title": f"Problem {pid}",
        "description": "desc",
        "input_description": "in desc",
        "output_description": "out desc",
        "samples": [{"input": "1\n", "output": "2\n"}],
        "constraints": None,
        "time_limit": 1.0,
        "memory_limit": 128,
        "difficulty": "easy",
        "tags": ["t1"],
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
def _make_test_cases():
    return [
        {"case_id": "c1", "input": "1\n", "output": "2\n", "score": 50, "is_hidden": False},
        {"case_id": "c2", "input": "3\n", "output": "4\n", "score": 50, "is_hidden": True},
    ]
async def test_create_and_get(fresh_db):
    p = _make_problem()
    await problem_repository.create(p, _make_test_cases())
    fetched = await problem_repository.get("P1001")
    assert fetched is not None
    assert fetched["title"] == "Problem P1001"
    assert fetched["samples"] == [{"input": "1\n", "output": "2\n"}]
    assert fetched["tags"] == ["t1"]
    assert fetched["constraints"] is None
    cases = await problem_repository.get_test_cases("P1001")
    assert len(cases) == 2
    assert cases[0]["case_id"] == "c1"
    assert cases[0]["is_hidden"] is False
    assert cases[1]["is_hidden"] is True
async def test_list_with_pagination(fresh_db):
    for i in range(5):
        p = _make_problem(f"P{i}")
        await problem_repository.create(p, _make_test_cases())
    items, total = await problem_repository.list(page=1, page_size=3)
    assert total == 5
    assert len(items) == 3
    items, total = await problem_repository.list(page=2, page_size=3)
    assert total == 5
    assert len(items) == 2
async def test_get_nonexistent(fresh_db):
    assert await problem_repository.get("nope") is None
    assert await problem_repository.exists("nope") is False
async def test_create_duplicate_id_raises(fresh_db):
    p = _make_problem()
    await problem_repository.create(p, _make_test_cases())
    with pytest.raises(Exception):
        await problem_repository.create(p, _make_test_cases())
async def test_update_replaces_test_cases(fresh_db):
    p = _make_problem()
    await problem_repository.create(p, _make_test_cases())
    updates = {
        "title": "Updated Title",
        "description": "new desc",
        "input_description": "new in",
        "output_description": "new out",
        "samples": [{"input": "x\n", "output": "y\n"}],
        "constraints": "new constraints",
        "time_limit": 2.0,
        "memory_limit": 256,
        "difficulty": "hard",
        "tags": ["new"],
        "updated_at": now_utc(),
    }
    new_tcs = [
        {"case_id": "x1", "input": "x\n", "output": "y\n", "score": 100, "is_hidden": False},
    ]
    ok = await problem_repository.update("P1001", updates, new_tcs)
    assert ok is True
    fetched = await problem_repository.get("P1001")
    assert fetched["title"] == "Updated Title"
    assert fetched["difficulty"] == "hard"
    assert fetched["constraints"] == "new constraints"
    cases = await problem_repository.get_test_cases("P1001")
    assert len(cases) == 1
    assert cases[0]["case_id"] == "x1"
async def test_update_nonexistent_returns_false(fresh_db):
    ok = await problem_repository.update("nope", _make_problem(), _make_test_cases())
    assert ok is False
async def test_delete_cascades_test_cases(fresh_db):
    p = _make_problem()
    await problem_repository.create(p, _make_test_cases())
    ok = await problem_repository.delete("P1001")
    assert ok is True
    assert await problem_repository.get("P1001") is None
    assert await problem_repository.get_test_cases("P1001") == []
async def test_delete_nonexistent_returns_false(fresh_db):
    ok = await problem_repository.delete("nope")
    assert ok is False