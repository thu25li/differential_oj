import pytest
from app.repositories.case_log_repository import case_log_repository
from app.repositories.submission_repository import submission_repository
from app.utils.id_gen import generate_uuid
from app.utils.time import now_utc
async def _make_submission(pid="P1", uid="u1"):
    s = {
        "id": generate_uuid(),
        "user_id": uid,
        "problem_id": pid,
        "language": "python",
        "source_code": "print(1)\n",
        "status": "pending",
        "created_at": now_utc(),
    }
    await submission_repository.create(s)
    return s["id"]
def _make_log(submission_id, case_id="c1", result="AC", is_hidden=False):
    return {
        "submission_id": submission_id,
        "case_id": case_id,
        "result": result,
        "score": 100 if result == "AC" else 0,
        "time_used": 0.05,
        "memory_used": None,
        "exit_code": 0,
        "input_data": "1 2\n",
        "stdout": "3\n",
        "stderr": "",
        "expected_output": "3\n",
        "message": "accepted",
        "is_hidden": is_hidden,
        "created_at": now_utc(),
    }
async def test_create_batch_and_get(fresh_db):
    sub_id = await _make_submission()
    logs = [
        _make_log(sub_id, case_id="c1", result="AC"),
        _make_log(sub_id, case_id="c2", result="WA", is_hidden=True),
    ]
    await case_log_repository.create_batch(logs)
    fetched = await case_log_repository.get_by_submission(sub_id)
    assert len(fetched) == 2
    assert fetched[0]["case_id"] == "c1"
    assert fetched[0]["result"] == "AC"
    assert fetched[1]["is_hidden"] is True
async def test_get_nonexistent_returns_empty(fresh_db):
    assert await case_log_repository.get_by_submission("nope") == []
async def test_delete_by_submission(fresh_db):
    sub_id = await _make_submission()
    await case_log_repository.create_batch([_make_log(sub_id)])
    deleted = await case_log_repository.delete_by_submission(sub_id)
    assert deleted == 1
    assert await case_log_repository.get_by_submission(sub_id) == []
async def test_list_with_submission_filter(fresh_db):
    s1 = await _make_submission(pid="P1")
    s2 = await _make_submission(pid="P2")
    await case_log_repository.create_batch([_make_log(s1), _make_log(s2)])
    items, total = await case_log_repository.list(submission_id=s1)
    assert total == 1
    assert items[0]["submission_id"] == s1
async def test_list_with_problem_filter(fresh_db):
    s1 = await _make_submission(pid="P1")
    s2 = await _make_submission(pid="P2")
    await case_log_repository.create_batch([_make_log(s1), _make_log(s2)])
    items, total = await case_log_repository.list(problem_id="P1")
    assert total == 1
    assert items[0]["submission_id"] == s1
async def test_list_with_user_filter(fresh_db):
    s1 = await _make_submission(pid="P1", uid="alice")
    s2 = await _make_submission(pid="P1", uid="bob")
    await case_log_repository.create_batch([_make_log(s1), _make_log(s2)])
    items, total = await case_log_repository.list(user_id="alice")
    assert total == 1
async def test_list_with_result_filter(fresh_db):
    s1 = await _make_submission()
    await case_log_repository.create_batch([
        _make_log(s1, case_id="c1", result="AC"),
        _make_log(s1, case_id="c2", result="WA"),
    ])
    items, total = await case_log_repository.list(result="AC")
    assert total == 1
    assert items[0]["result"] == "AC"
async def test_list_pagination(fresh_db):
    sub_id = await _make_submission()
    logs = [_make_log(sub_id, case_id=f"c{i}", result="AC") for i in range(5)]
    await case_log_repository.create_batch(logs)
    items, total = await case_log_repository.list(page=2, page_size=2)
    assert total == 5
    assert len(items) == 2
